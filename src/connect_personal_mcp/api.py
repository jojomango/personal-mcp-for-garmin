"""Client for the official Garmin Connect Personal API.

Auth flow (per Garmin's Personal API FAQ):
  personal API key --POST token endpoint, "Authorization: ApiKey <key>"--> OAuth2 access token
  The access token is valid for 24h (or until the key expires). There is no refresh token;
  you simply request a new one.

Only the Python standard library is used, so nothing but Garmin's own host is contacted.
"""

from __future__ import annotations

import json
import os
import stat
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from . import __version__

CONFIG_DIR = Path(os.path.expanduser(os.getenv("GARMIN_MCP_CONFIG_DIR", "~/.config/connect-personal-mcp")))
KEY_FILE = CONFIG_DIR / "personal_api_key"
_LEGACY_KEY_FILE = Path(os.path.expanduser("~/.config/garmin-mcp/personal_api_key"))  # pre-0.3 location

KEY_PAGE = "https://connect.garmin.com/app/settings/personalApiToken"
_BASES = {
    "global": "https://personal.connectapi.garmin.com",
    "cn": "https://personal.connectapi.garmin.cn",
}
TOKEN_PATH = "/personalapitoken-service/personal-api/personal-api-key/token"
TOKEN_TTL = 23 * 3600  # docs say 24h; renew an hour early
USER_AGENT = f"connect-personal-mcp/{__version__} (personal use)"
# Garmin may throttle without notice, so identical requests within this window reuse the result.
CACHE_TTL = float(os.getenv("GARMIN_CACHE_TTL", "300"))


class GarminAPIError(Exception):
    def __init__(self, status: int | None, message: str):
        super().__init__(message)
        self.status = status


def base_url() -> str:
    if os.getenv("GARMIN_API_BASE"):  # used by the offline tests
        return os.environ["GARMIN_API_BASE"].rstrip("/")
    region = os.getenv("GARMIN_REGION", "global").strip().lower() or "global"
    if region not in _BASES:
        raise GarminAPIError(None, f"Unknown GARMIN_REGION {region!r}; use 'global' or 'cn'.")
    return _BASES[region]


def load_api_key() -> str | None:
    key = os.getenv("GARMIN_API_KEY", "").strip()
    if key:
        return key
    for f in (KEY_FILE, _LEGACY_KEY_FILE):
        if f.is_file() and (k := f.read_text().strip()):
            return k
    return None


def save_api_key(key: str) -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    os.chmod(CONFIG_DIR, stat.S_IRWXU)
    KEY_FILE.write_text(key.strip() + "\n")
    os.chmod(KEY_FILE, stat.S_IRUSR | stat.S_IWUSR)
    return KEY_FILE


def _extract_token(body: bytes) -> tuple[str, float | None]:
    """Garmin doesn't document the token response shape, so accept the common ones."""
    text = body.decode("utf-8", "replace").strip()
    if text.lower().startswith("bearer "):
        text = text[7:].strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        if text and " " not in text:
            return text, None  # plain-text token
        raise GarminAPIError(None, "Unexpected token response format.")
    if isinstance(data, str):
        return data, None
    if isinstance(data, dict):
        for k in ("access_token", "accessToken", "token"):
            if isinstance(data.get(k), str):
                exp = data.get("expires_in") or data.get("expiresIn")
                return data[k], float(exp) if isinstance(exp, (int, float)) else None
        # field names only, never values
        raise GarminAPIError(None, f"Token response has no access token field (fields: {sorted(data)}).")
    raise GarminAPIError(None, "Unexpected token response format.")


class PersonalAPI:
    def __init__(self, api_key: str, timeout: float = 30):
        self._key = api_key
        self._timeout = timeout
        self._token: str | None = None
        self._token_until = 0.0
        self._lock = threading.Lock()
        self._cache: dict[str, tuple[float, Any]] = {}

    # ---------- auth ----------
    def _fetch_token(self) -> None:
        req = urllib.request.Request(
            base_url() + TOKEN_PATH, method="POST", data=b"",
            # Garmin answers 406 to "Accept: application/json" here because the token isn't
            # served as JSON. Match the documented curl call, which sends */*.
            headers={"Authorization": f"ApiKey {self._key}", "Accept": "*/*", "User-Agent": USER_AGENT},
        )
        status, body, _ = self._send(req)
        if status in (401, 403):
            raise GarminAPIError(status, f"API key is invalid, expired or deleted. Create a new one at {KEY_PAGE} "
                                         "and run `uv run connect-personal-mcp-setup`.")
        if status >= 400:
            raise GarminAPIError(status, f"Could not get an access token (HTTP {status}): "
                                         f"{body[:300].decode('utf-8', 'replace')}")
        token, ttl = _extract_token(body)
        self._token = token
        self._token_until = time.time() + min(ttl - 300 if ttl else TOKEN_TTL, TOKEN_TTL)

    def _bearer(self, force: bool = False) -> str:
        with self._lock:
            if force or not self._token or time.time() >= self._token_until:
                self._fetch_token()
            return self._token  # type: ignore[return-value]

    # ---------- http ----------
    def _send(self, req: urllib.request.Request) -> tuple[int, bytes, dict[str, str]]:
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as r:
                return r.status, r.read(), dict(r.headers)
        except urllib.error.HTTPError as e:
            return e.code, e.read(), dict(e.headers or {})
        except urllib.error.URLError as e:
            raise GarminAPIError(None, f"Connection failed: {e.reason}") from e

    def request(self, path: str, params: dict[str, Any] | None = None, raw: bool = False) -> Any:
        q = {k: (str(v).lower() if isinstance(v, bool) else v) for k, v in (params or {}).items() if v is not None}
        url = base_url() + path + ("?" + urllib.parse.urlencode(q, doseq=True) if q else "")

        if not raw and CACHE_TTL > 0:
            hit = self._cache.get(url)
            if hit and hit[0] > time.time():
                return hit[1]

        for attempt in (0, 1):
            req = urllib.request.Request(url, headers={
                "Authorization": f"Bearer {self._bearer(force=attempt == 1)}",
                # prefer JSON but never trigger a 406 if an endpoint serves something else
                "Accept": "*/*" if raw else "application/json, */*;q=0.5",
                "User-Agent": USER_AGENT,
            })
            status, body, headers = self._send(req)
            if status == 401 and attempt == 0:
                continue  # token expired early: fetch a new one and retry once
            break
        if status == 429:
            raise GarminAPIError(429, "Rate limited by Garmin; try again later "
                                      f"(Retry-After: {headers.get('Retry-After', '?')}).")
        if status >= 400:
            raise GarminAPIError(status, f"HTTP {status} {path}: {body[:500].decode('utf-8', 'replace')}")
        if raw:
            return body, headers

        if not body:
            data = None
        else:
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                data = body.decode("utf-8", "replace")
        if CACHE_TTL > 0:
            if len(self._cache) > 256:
                self._cache.clear()
            self._cache[url] = (time.time() + CACHE_TTL, data)
        return data
