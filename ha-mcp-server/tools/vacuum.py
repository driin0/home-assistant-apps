import httpx

from tools._base import mcp, HA_URL, HEADERS


def _resolve_vacuum(entity_id: str) -> str:
    """Return entity_id, or the first vacuum entity found when it is empty."""
    if entity_id:
        return entity_id
    with httpx.Client() as client:
        r = client.get(f"{HA_URL}/api/states", headers=HEADERS, timeout=15)
        r.raise_for_status()
    for s in r.json():
        if s["entity_id"].startswith("vacuum."):
            return s["entity_id"]
    return ""


@mcp.tool()
def get_vacuum_state(entity_id: str = "") -> dict:
    """
    Get the current state and attributes of a vacuum robot.

    entity_id: vacuum entity; leave empty to use the first one found.
    """
    entity_id = _resolve_vacuum(entity_id)
    if not entity_id:
        return {"error": "no_vacuum_found", "detail": "No vacuum.* entity exists on this instance."}
    with httpx.Client() as client:
        r = client.get(f"{HA_URL}/api/states/{entity_id}", headers=HEADERS, timeout=10)
        r.raise_for_status()
        s = r.json()
        attrs = s.get("attributes", {})
        return {
            "entity_id": s["entity_id"],
            "state": s["state"],
            "battery_level": attrs.get("battery_level"),
            "fan_speed": attrs.get("fan_speed"),
            "status": attrs.get("status"),
            "cleaning_mode": attrs.get("cleaning_mode"),
            "current_room": attrs.get("current_room"),
            "cleaned_area": attrs.get("cleaned_area"),
            "error": attrs.get("error"),
            "last_changed": s.get("last_changed", ""),
        }


@mcp.tool()
def vacuum_control(
    command: str,
    entity_id: str = "",
    rooms: list = None,
    fan_speed: str = "",
) -> dict:
    """
    Control a vacuum robot.

    entity_id: vacuum entity; leave empty to use the first one found.

    command:
      - 'start'       start cleaning (whole house)
      - 'stop'        stop cleaning
      - 'pause'       pause cleaning
      - 'return'      return to base/dock
      - 'locate'      play locate sound
      - 'fan_speed'   set fan speed (requires fan_speed: 'quiet'|'standard'|'strong'|'turbo')
      - 'clean_rooms' clean specific rooms (requires rooms: list of room names)
    """
    entity_id = _resolve_vacuum(entity_id)
    if not entity_id:
        return {"error": "no_vacuum_found", "detail": "No vacuum.* entity exists on this instance."}
    with httpx.Client() as client:
        if command == "start":
            r = client.post(f"{HA_URL}/api/services/vacuum/start",
                            headers=HEADERS, json={"entity_id": entity_id}, timeout=10)
        elif command == "stop":
            r = client.post(f"{HA_URL}/api/services/vacuum/stop",
                            headers=HEADERS, json={"entity_id": entity_id}, timeout=10)
        elif command == "pause":
            r = client.post(f"{HA_URL}/api/services/vacuum/pause",
                            headers=HEADERS, json={"entity_id": entity_id}, timeout=10)
        elif command == "return":
            r = client.post(f"{HA_URL}/api/services/vacuum/return_to_base",
                            headers=HEADERS, json={"entity_id": entity_id}, timeout=10)
        elif command == "locate":
            r = client.post(f"{HA_URL}/api/services/vacuum/locate",
                            headers=HEADERS, json={"entity_id": entity_id}, timeout=10)
        elif command == "fan_speed" and fan_speed:
            r = client.post(f"{HA_URL}/api/services/vacuum/set_fan_speed",
                            headers=HEADERS,
                            json={"entity_id": entity_id, "fan_speed": fan_speed}, timeout=10)
        elif command == "clean_rooms" and rooms:
            r = client.post(f"{HA_URL}/api/services/dreame_vacuum/vacuum_clean_segment",
                            headers=HEADERS,
                            json={"entity_id": entity_id, "segments": rooms}, timeout=10)
        else:
            return {"error": f"Unknown command or missing parameters: {command}"}
        r.raise_for_status()
        return {"command": command, "entity_id": entity_id, "ok": True}


@mcp.tool()
def vacuum_room(
    rooms: list,
    entity_id: str = "",
    repeats: int = 1,
) -> dict:
    """
    Clean one or more specific rooms (segments) with a Dreame vacuum.

    rooms:     list of segment IDs (integers), e.g. [1, 3].
               Find segment IDs from the vacuum map in the Dreame integration:
               HA → Settings → Devices → your vacuum → vacuum_clean_segment
               service, or from get_vacuum_state() attributes
               (segment_status / map_data).
    repeats:   number of cleaning passes (default 1, max typically 3)
    entity_id: vacuum entity; leave empty to use the first one found.
    """
    entity_id = _resolve_vacuum(entity_id)
    if not entity_id:
        return {"error": "no_vacuum_found", "detail": "No vacuum.* entity exists on this instance."}
    with httpx.Client() as client:
        payload: dict = {"entity_id": entity_id, "segments": rooms}
        if repeats > 1:
            payload["repeats"] = repeats
        r = client.post(
            f"{HA_URL}/api/services/dreame_vacuum/vacuum_clean_segment",
            headers=HEADERS,
            json=payload,
            timeout=10,
        )
        r.raise_for_status()
    return {"entity_id": entity_id, "rooms": rooms, "repeats": repeats, "ok": True}
