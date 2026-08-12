import httpx

from tools._base import mcp, HA_URL, HEADERS


@mcp.tool()
def list_covers() -> list:
    """List all cover entities (blinds, shutters, garage doors, etc.) with state and position."""
    with httpx.Client() as client:
        r = client.get(f"{HA_URL}/api/states", headers=HEADERS, timeout=15)
        r.raise_for_status()
    covers = []
    for s in r.json():
        if not s["entity_id"].startswith("cover."):
            continue
        attrs = s.get("attributes", {})
        covers.append({
            "entity_id": s["entity_id"],
            "name": attrs.get("friendly_name", s["entity_id"]),
            "state": s["state"],
            "position": attrs.get("current_position"),
            "tilt_position": attrs.get("current_tilt_position"),
            "device_class": attrs.get("device_class"),
        })
    return sorted(covers, key=lambda x: x["name"])


@mcp.tool()
def cover_control(
    entity_id: str,
    command: str,
    position: int = None,
    tilt_position: int = None,
) -> dict:
    """
    Control a cover entity (blind, shutter, garage door, etc.).

    command: open | close | stop | set_position | set_tilt_position | toggle
    position: 0–100, used with set_position
    tilt_position: 0–100, used with set_tilt_position
    """
    command_map = {
        "open": "open_cover",
        "close": "close_cover",
        "stop": "stop_cover",
        "toggle": "toggle",
        "set_position": "set_cover_position",
        "set_tilt_position": "set_cover_tilt_position",
    }
    service = command_map.get(command)
    if not service:
        raise ValueError(f"Unknown command '{command}'. Use: {', '.join(command_map)}")
    data: dict = {"entity_id": entity_id}
    if command == "set_position" and position is not None:
        data["position"] = position
    if command == "set_tilt_position" and tilt_position is not None:
        data["tilt_position"] = tilt_position
    with httpx.Client() as client:
        r = client.post(f"{HA_URL}/api/services/cover/{service}", headers=HEADERS, json=data, timeout=10)
        r.raise_for_status()
    return {"entity_id": entity_id, "command": command, "ok": True}
