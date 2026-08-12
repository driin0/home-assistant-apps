import httpx
from datetime import datetime, timezone, timedelta

from tools._base import mcp, HA_URL, HEADERS, _ws


@mcp.tool()
def list_calendars() -> list:
    """List all calendar entities."""
    with httpx.Client() as client:
        r = client.get(f"{HA_URL}/api/calendars", headers=HEADERS, timeout=10)
        r.raise_for_status()
        return r.json()


@mcp.tool()
def get_calendar_events(entity_id: str, start: str = "", end: str = "") -> list:
    """
    Get events from a calendar entity.

    entity_id: e.g. 'calendar.home'
    start: ISO8601 datetime (default: now)
    end: ISO8601 datetime (default: 7 days from now)
    """
    now = datetime.now(timezone.utc)
    start_dt = start or now.isoformat()
    end_dt = end or (now + timedelta(days=7)).isoformat()
    with httpx.Client() as client:
        r = client.get(
            f"{HA_URL}/api/calendars/{entity_id}",
            headers=HEADERS,
            params={"start": start_dt, "end": end_dt},
            timeout=10,
        )
        r.raise_for_status()
        return r.json()


@mcp.tool()
def add_calendar_event(
    entity_id: str,
    summary: str,
    start: str,
    end: str,
    description: str = "",
    location: str = "",
    all_day: bool = False,
) -> dict:
    """
    Create a new event on a calendar entity.

    entity_id:   e.g. 'calendar.home'
    summary:     event title
    start:       ISO8601 datetime e.g. '2026-04-15T10:00:00+02:00' (or 'YYYY-MM-DD' if all_day)
    end:         ISO8601 datetime e.g. '2026-04-15T11:00:00+02:00' (or 'YYYY-MM-DD' if all_day)
    description: optional notes
    location:    optional location string
    all_day:     if True uses date-only format (start/end as 'YYYY-MM-DD')
    """
    payload: dict = {"entity_id": entity_id, "summary": summary}
    if all_day:
        payload["start_date"] = start[:10]
        payload["end_date"] = end[:10]
    else:
        payload["start_date_time"] = start
        payload["end_date_time"] = end
    if description:
        payload["description"] = description
    if location:
        payload["location"] = location

    with httpx.Client() as client:
        r = client.post(
            f"{HA_URL}/api/services/calendar/create_event",
            headers=HEADERS,
            json=payload,
            timeout=10,
        )
        r.raise_for_status()
    return {
        "created": True,
        "entity_id": entity_id,
        "summary": summary,
        "start": start,
        "end": end,
    }
