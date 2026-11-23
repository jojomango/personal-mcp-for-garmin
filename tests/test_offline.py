"""Offline tests: run the server's tools against a local mock of Garmin's Personal API.

    uv run python -m unittest discover -s tests

No API key or network access to Garmin is needed.
"""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

GOOD_KEY = "test-key"


class MockGarmin(BaseHTTPRequestHandler):
    """Mimics the behaviour observed on the real API (e.g. 406 for a JSON Accept on the token call)."""

    tokens = 0
    expire_next = False
    hits: list[str] = []

    def log_message(self, *args):  # keep test output quiet
        pass

    def _send(self, code, body, ctype="application/json", extra=None):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if not self.path.endswith("/personal-api-key/token"):
            return self._send(404, {})
        if self.headers.get("Authorization") != f"ApiKey {GOOD_KEY}":
            return self._send(401, {"error": "unauthorized"})
        if self.headers.get("Accept") == "application/json":
            return self._send(406, {"error": "NotAcceptableException"})
        MockGarmin.tokens += 1
        return self._send(200, f"tok{MockGarmin.tokens}".encode(), "text/plain")

    def do_GET(self):
        u = urlparse(self.path)
        MockGarmin.hits.append(u.path)
        if MockGarmin.expire_next:
            MockGarmin.expire_next = False
            return self._send(401, {"error": "expired"})
        if self.headers.get("Authorization") != f"Bearer tok{MockGarmin.tokens}":
            return self._send(401, {"error": "bad bearer"})
        if u.path.startswith("/download-service/"):
            return self._send(200, b"PK\x03\x04fit", "application/zip",
                              {"Content-Disposition": 'attachment; filename="123.zip"'})
        if u.path == "/activitylist-service/activities/search/activities":
            return self._send(200, [{
                "activityId": 123, "activityName": "Morning Run", "activityType": {"typeKey": "running"},
                "averageSpeed": 2.5, "hrTimeInZone_1": 60.4, "hrTimeInZone_2": 120.0,
                "ownerFullName": "Should Not Appear In Compact",
            }])
        return self._send(200, {"path": u.path, "query": parse_qs(u.query)})


class OfflineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = HTTPServer(("127.0.0.1", 0), MockGarmin)
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()
        cls.tmp = tempfile.mkdtemp()
        os.environ.update({
            "GARMIN_API_BASE": f"http://127.0.0.1:{cls.httpd.server_port}",
            "GARMIN_API_KEY": GOOD_KEY,
            "GARMIN_MCP_CONFIG_DIR": os.path.join(cls.tmp, "config"),
            "GARMIN_DOWNLOAD_DIR": os.path.join(cls.tmp, "downloads"),
        })
        from connect_personal_mcp import api as api_mod, server
        api_mod._LEGACY_KEY_FILE = Path(cls.tmp, "no-legacy-key")  # never read a real key on the dev machine
        cls.api_mod, cls.server = api_mod, server

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def setUp(self):
        os.environ["GARMIN_API_KEY"] = GOOD_KEY
        self.server.api.cache_clear()
        MockGarmin.hits.clear()

    def test_token_exchange_and_attribution(self):
        r = self.server.daily_summary(start="2026-11-20")
        self.assertEqual(r["data_source"], "Garmin")
        self.assertEqual(r["data"]["path"], "/usersummary-service/usersummary/daily")
        self.assertEqual(r["data"]["query"], {"calendarDate": ["2026-11-20"]})

    def test_range_uses_range_endpoint(self):
        r = self.server.sleep(start="2026-11-16", end="2026-11-22")
        self.assertEqual(r["data"]["path"], "/sleep-service/sleep/dailySleepSummariesByDate")

    def test_identical_requests_are_cached(self):
        self.server.hrv(start="2026-11-01")
        self.server.hrv(start="2026-11-01")
        self.assertEqual(MockGarmin.hits.count("/hrv-service/hrv/2026-11-01"), 1)

    def test_expired_token_is_renewed_once(self):
        self.server.heart_rate(day="2026-11-01")  # warm up: this client fetches its first token
        before = MockGarmin.tokens
        MockGarmin.expire_next = True
        r = self.server.heart_rate(day="2026-11-02")
        self.assertIn("data", r)
        self.assertEqual(MockGarmin.tokens, before + 1)

    def test_compact_activities(self):
        row = self.server.activities(limit=1)["data"][0]
        self.assertEqual(row["activityType"], "running")
        self.assertEqual(row["avgPacePerKm"], "6:40")
        self.assertEqual(row["hrTimeInZoneSeconds"]["z1"], 60)
        self.assertNotIn("ownerFullName", row)

    def test_bad_date_returns_error(self):
        self.assertIn("Invalid argument", self.server.sleep(start="not-a-date")["error"])

    def test_bad_key_returns_error(self):
        os.environ["GARMIN_API_KEY"] = "wrong"
        r = self.server.user_settings()
        self.assertEqual(r["status"], 401)
        self.assertIn("invalid", r["error"])

    def test_missing_key_returns_error(self):
        os.environ["GARMIN_API_KEY"] = ""
        self.assertIn("No Garmin Personal API key", self.server.user_settings()["error"])

    def test_download_writes_file(self):
        r = self.server.download_activity_file(activity_id=123)["data"]
        self.assertTrue(Path(r["saved_to"]).read_bytes().startswith(b"PK"))

    def test_tool_annotations(self):
        tools = asyncio.run(self.server.mcp.list_tools())
        for t in tools:
            self.assertTrue(t.annotations and t.annotations.title, t.name)
            self.assertFalse(t.annotations.destructive_hint, t.name)
            self.assertEqual(t.annotations.read_only_hint, t.name != "download_activity_file", t.name)

    def test_manifest_lists_every_tool(self):
        manifest = json.loads(Path(__file__).parents[1].joinpath("manifest.json").read_text())
        tools = asyncio.run(self.server.mcp.list_tools())
        self.assertEqual({t["name"] for t in manifest["tools"]}, {t.name for t in tools})


if __name__ == "__main__":
    unittest.main()
