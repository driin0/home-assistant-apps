import httpx

from tools._base import mcp, HA_URL, HEADERS


@mcp.tool()
def list_fans() -> list:
    """List all fan entities with state and speed."""
    with httpx.Client() as client:
        r = client.get(f"{HA_URL}/api/states", headers=HEADERS, timeout=15)
        r.raise_for_status()
    fans = []
    for s in r.json():
        if not s["entity_id"].startswith("fan."):
            continue
        attrs = s.get("attributes", {})
        fans.append({
            "entity_id": s["entity_id"],
            "name": attrs.get("friendly_name", s["entity_id"]),
            "state": s["state"],
            "percentage": attrs.get("percentage"),
            "preset_mode": attrs.get("preset_mode"),
            "preset_modes": attrs.get("preset_modes", []),
            "oscillating": attrs.get("oscillating"),
            "direction": attrs.get("direction"),
        })
    return sorted(fans, key=lambda x: x["name"])


@mcp.tool()
def fan_control(
    entity_id: str,
    command: str,
    percentage: int = None,
    preset_mode: str = "",
    oscillating: bool = None,
    direction: str = "",
) -> dict:
    """
    Control a fan entity.

    command: turn_on | turn_off | toggle | set_percentage | set_preset_mode | oscillate | set_direction
    percentage: 0–100, speed percentage
    preset_mode: e.g. 'auto', 'sleep'
    oscillating: true/false
    direction: forward | reverse
    """
    service_map = {
        "turn_on": "turn_on",
        "turn_off": "turn_off",
        "toggle": "toggle",
        "set_percentage": "set_percentage",
        "set_preset_mode": "set_preset_mode",
        "oscillate": "oscillate",
        "set_direction": "set_direction",
    }
    service = service_map.get(command)
    if not service:
        raise ValueError(f"Unknown command '{command}'. Use: {', '.join(service_map)}")
    data: dict = {"entity_id": entity_id}
    if percentage is not None:
        data["percentage"] = percentage
    if preset_mode:
        data["preset_mode"] = preset_mode
    if oscillating is not None:
        data["oscillating"] = oscillating
    if direction:
        data["direction"] = direction
    with httpx.Client() as client:
        r = client.post(f"{HA_URL}/api/services/fan/{service}", headers=HEADERS, json=data, timeout=10)
        r.raise_for_status()
    return {"entity_id": entity_id, "command": command, "ok": True}
