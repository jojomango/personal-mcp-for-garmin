"""MCP server (stdio) exposing your own Garmin Connect™ data via Garmin's official Personal API.

Unofficial; not affiliated with or endorsed by Garmin. Read-only: no tool changes anything in
your Garmin account. Every successful result is wrapped as {"data_source": "Garmin", "data": ...}
to satisfy Garmin's API Brand Guidelines (attribute Garmin as the data source; the Personal API
does not expose the device model, so "Garmin" is used).
"""

from __future__ import annotations

import functools
import os
import re
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

from .api import KEY_PAGE, GarminAPIError, PersonalAPI, load_api_key

DOWNLOAD_DIR = Path(os.path.expanduser(os.getenv("GARMIN_DOWNLOAD_DIR", "~/Downloads/garmin")))
DATA_SOURCE = "Garmin"

mcp = MCPServer(
    "connect-personal",
    instructions=(
        "Read-only access to the user's own Garmin Connect health and activity data through Garmin's "
        "official Personal API. Dates are YYYY-MM-DD, 'today' or 'yesterday'. For several days, prefer "
        "one call with start and end over many single-day calls. "
        "Every result carries data_source='Garmin': when you present, chart or analyse this data, "
        "state that the data source is Garmin (for example 'Data source: Garmin')."
    ),
)


# ---------- helpers ----------

def tool(title: str, *, read_only: bool = True) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Register an MCP tool with a title and safety annotations.

    Successful results are wrapped with Garmin attribution; bad arguments and API failures come
    back as {"error": ...} instead of raising, so the model sees a readable message.
    """
    annotations = ToolAnnotations(
        title=title,
        read_only_hint=read_only,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=True,
    )

    def decorate(fn: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                result = fn(*args, **kwargs)
            except ValueError as e:
                return {"error": f"Invalid argument: {e} (dates must be YYYY-MM-DD, 'today' or 'yesterday')."}
            except GarminAPIError as e:
                return {"error": str(e), "status": e.status}
            return {"data_source": DATA_SOURCE, "data": result}

        return mcp.tool(title=title, annotations=annotations)(wrapper)

    return decorate


def _d(day: str | None) -> str | None:
    """None -> None; 'today'/'yesterday' -> ISO date; otherwise validate YYYY-MM-DD."""
    if day is None:
        return None
    day = day.strip().lower()
    if day in ("", "today"):
        return date.today().isoformat()
    if day == "yesterday":
        return (date.today() - timedelta(days=1)).isoformat()
    return date.fromisoformat(day).isoformat()


def _range(start: str, end: str | None) -> tuple[str, str]:
    s = _d(start)
    return s, _d(end) if end else s  # type: ignore[return-value]


@lru_cache(maxsize=1)
def api() -> PersonalAPI:
    key = load_api_key()
    if not key:
        api.cache_clear()
        raise GarminAPIError(
            None,
            f"No Garmin Personal API key configured. Create one at {KEY_PAGE}, then run "
            "`uv run connect-personal-mcp-setup` (or set GARMIN_API_KEY).",
        )
    return PersonalAPI(key)


def _get(path: str, **params: Any) -> Any:
    try:
        return api().request(path, params)
    except GarminAPIError:
        if load_api_key() is None:
            api.cache_clear()
        raise


# ---------- daily health ----------

@tool("Daily summary")
def daily_summary(start: str = "today", end: str | None = None) -> Any:
    """Daily overview: steps, distance, calories, resting heart rate, stress, Body Battery,
    intensity minutes, floors. Give only start for one day, or start+end for a daily list."""
    if end is None:
        return _get("/usersummary-service/usersummary/daily", calendarDate=_d(start))
    s, e = _range(start, end)
    return _get("/usersummary-service/v2/dailysummaries", startDate=s, endDate=e)


@tool("Sleep")
def sleep(start: str = "today", end: str | None = None) -> Any:
    """Sleep: duration, deep/light/REM/awake stages, sleep score and feedback. The date is the day
    you woke up. Only start: detailed single night; start+end: summaries for the range."""
    if end is None:
        return _get("/sleep-service/sleep/dailySleep", date=_d(start))
    s, e = _range(start, end)
    return _get("/sleep-service/sleep/dailySleepSummariesByDate", startDate=s, endDate=e)


@tool("Heart rate")
def heart_rate(day: str = "today") -> Any:
    """One day of heart rate: resting, max, min and the all-day time series."""
    return _get("/wellness-service/wellness/dailyHeartRate", date=_d(day))


@tool("Heart rate variability")
def hrv(start: str = "today", end: str | None = None) -> Any:
    """HRV: overnight average, baseline range and status. Only start: single-day detail;
    start+end: daily summaries."""
    if end is None:
        return _get(f"/hrv-service/hrv/{_d(start)}")
    s, e = _range(start, end)
    return _get(f"/hrv-service/hrv/daily/{s}/{e}")


@tool("Body Battery")
def body_battery(start: str = "today", end: str | None = None) -> Any:
    """Daily Body Battery reports (charged, drained, highs and lows)."""
    s, e = _range(start, end)
    return _get("/wellness-service/wellness/bodyBattery/reports/daily", startDate=s, endDate=e)


@tool("Stress")
def stress(start: str, end: str | None = None) -> Any:
    """Daily stress statistics for a date range."""
    s, e = _range(start, end)
    return _get(f"/usersummary-service/stats/stress/daily/{s}/{e}")


@tool("Steps")
def steps(start: str, end: str | None = None) -> Any:
    """Daily steps, distance and step goal for a date range."""
    s, e = _range(start, end)
    return _get(f"/usersummary-service/stats/steps/daily/{s}/{e}")


@tool("Hydration")
def hydration(start: str, end: str | None = None) -> Any:
    """Daily hydration logs for a date range."""
    s, e = _range(start, end)
    return _get(f"/usersummary-service/stats/hydration/daily/{s}/{e}")


@tool("Pulse Ox and acclimation")
def spo2_acclimation(day: str = "today") -> Any:
    """Blood oxygen (SpO2) and altitude acclimation for one day."""
    return _get(f"/wellness-service/wellness/daily/spo2acclimation/{_d(day)}")


@tool("Weight and body composition")
def weight(start: str, end: str | None = None) -> Any:
    """Weight and body composition entries for a date range."""
    s, e = _range(start, end)
    return _get(f"/weight-service/weight/range/{s}/{e}", includeAll=True)


@tool("Weight goal")
def weight_goal(start: str, end: str | None = None) -> Any:
    """Weight goals in effect during a date range."""
    s, e = _range(start, end)
    return _get(f"/goal-service/goal/user/effective/weightgoal/{s}/{e}")


@tool("VO2 max")
def vo2max(start: str, end: str | None = None, sport: list[str] | None = None) -> Any:
    """Daily VO2 max (MaxMET) values. Optional sport filter, e.g. ["RUNNING"] or ["CYCLING"].
    Readings are only recorded on some days, so use a wide date range."""
    s, e = _range(start, end)
    return _get(f"/metrics-service/metrics/maxmet/daily/{s}/{e}", sport=sport)


@tool("Fitness age")
def fitness_age(day: str = "today") -> Any:
    """Fitness age and the factors behind it."""
    return _get(f"/fitnessage-service/fitnessage/v2/{_d(day)}")


@tool("Heart rate zones")
def heart_rate_zones() -> Any:
    """The user's configured heart rate zones."""
    return _get("/biometric-service/heartRateZones/v2")


@tool("Nutrition log")
def nutrition(day: str = "today") -> Any:
    """Food log and nutrition goals for one day."""
    return _get(f"/nutrition-service/food/logs/{_d(day)}", includeGoals=True, includeNutrition=True)


@tool("Menstrual cycle")
def menstrual_cycle(day: str = "today", detailed: bool = False) -> Any:
    """Menstrual cycle summary; detailed=True returns the detailed day view."""
    if detailed:
        return _get(f"/periodichealth-service/menstrualcycle/dayview/{_d(day)}")
    return _get(f"/periodichealth-service/menstrualcycle/summary/{_d(day)}")


@tool("User settings")
def user_settings() -> Any:
    """User settings: units, height, weight, birth date, sleep schedule, etc."""
    return _get("/userprofile-service/userprofile/settings")


# ---------- activities ----------

_ACTIVITY_KEEP = (
    "activityId", "activityName", "startTimeLocal", "activityType", "distance", "duration",
    "movingDuration", "averageHR", "maxHR", "calories", "averageSpeed", "elevationGain",
    "aerobicTrainingEffect", "anaerobicTrainingEffect", "avgPower", "vO2MaxValue",
    # cadence / stride (running: steps/min; cycling: rpm)
    "averageRunningCadenceInStepsPerMinute", "maxRunningCadenceInStepsPerMinute",
    "averageBikingCadenceInRevPerMinute", "avgStrideLength", "steps",
    # effort
    "trainingEffectLabel", "moderateIntensityMinutes", "vigorousIntensityMinutes",
    "fastestSplit_1000", "locationName", "lapCount",
)
_HR_ZONE_KEYS = tuple(f"hrTimeInZone_{i}" for i in range(1, 6))


def _compact_activity(a: dict[str, Any]) -> dict[str, Any]:
    row = {k: a[k] for k in _ACTIVITY_KEEP if a.get(k) is not None}
    if isinstance(row.get("activityType"), dict):
        row["activityType"] = row["activityType"].get("typeKey")
    if any(k in a for k in _HR_ZONE_KEYS):
        row["hrTimeInZoneSeconds"] = {f"z{i}": round(a.get(f"hrTimeInZone_{i}") or 0) for i in range(1, 6)}
    speed = a.get("averageSpeed")
    if speed:  # m/s -> min:sec per km, so the model doesn't have to convert
        sec = round(1000 / speed)
        row["avgPacePerKm"] = f"{sec // 60}:{sec % 60:02d}"
    return row


@tool("Search activities")
def activities(
    limit: int = 10,
    start_date: str | None = None,
    end_date: str | None = None,
    activity_type: str | None = None,
    search: str | None = None,
    compact: bool = True,
) -> Any:
    """Search activities, newest first. activity_type e.g. running, cycling, swimming (see
    activity_types). compact=True returns the common fields, including pace, heart rate zone
    seconds, cadence, stride and training effect; compact=False returns every field (including
    the owner's name and GPS start/end points). Use activity_detail for laps."""
    res = _get(
        "/activitylist-service/activities/search/activities",
        start=0, limit=max(1, min(limit, 100)),
        startDate=_d(start_date), endDate=_d(end_date),
        activityType=activity_type, search=search,
    )
    if not compact or not isinstance(res, list):
        return res
    return [_compact_activity(a) for a in res]


@tool("Activity detail")
def activity_detail(activity_id: int) -> Any:
    """Full summary of one activity: splits, heart rate, pace, training effect."""
    return _get(f"/activity-service/activity/{activity_id}")


@tool("Activity workouts")
def activity_workouts(activity_id: int) -> Any:
    """Workouts linked to one activity."""
    return _get(f"/activity-service/activity/{activity_id}/workouts")


@tool("Wellness activities")
def activity_summary_range(start: str, end: str | None = None) -> Any:
    """Wellness activity records (e.g. breathwork) in a date range. This is NOT a workout summary;
    use activities for runs, rides and other workouts."""
    s, e = _range(start, end)
    return _get(f"/wellnessactivity-service/activity/summary/range/{s}/{e}")


@tool("Activity types")
def activity_types() -> Any:
    """All supported activity types (the typeKey works as activities' activity_type)."""
    return _get("/activity-service/activity/activityTypes/simple")


@tool("Download activity file", read_only=False)
def download_activity_file(activity_id: int) -> Any:
    """Download one activity's original file (FIT, usually zipped) to the local Downloads/garmin
    folder and return its path. Writes a local file only; nothing changes in Garmin Connect."""
    body, headers = api().request(f"/download-service/files/activity/{activity_id}", raw=True)
    cd = headers.get("Content-Disposition") or headers.get("content-disposition") or ""
    m = re.search(r'filename="?([^";]+)"?', cd)
    ctype = (headers.get("Content-Type") or headers.get("content-type") or "").lower()
    name = Path(m.group(1)).name if m else f"{activity_id}{'.zip' if 'zip' in ctype else '.fit'}"
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    path = DOWNLOAD_DIR / name
    path.write_bytes(body)
    return {"saved_to": str(path), "bytes": len(body), "content_type": ctype}


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
