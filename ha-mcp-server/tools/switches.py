import httpx

from tools._base import mcp, HA_URL, HEADERS


@mcp.tool()
def list_switches() -> list:
    """List all switch entities with their current state."""
    with httpx.Client() as client:
        r = client.get(f"{HA_URL}/api/states", headers=HEADERS, timeout=15)
        r.raise_for_status()
    return sorted([
        {
            "entity_id": s["entity_id"],
            "name": s.get("attributes", {}).get("friendly_name", s["entity_id"]),
            "state": s["state"],
        }
        for s in r.json()
        if s["entity_id"].startswith("switch.")
    ], key=lambda x: x["name"])


@mcp.tool()
def toggle_entity(entity_id: str, state: str = "toggle") -> dict:
    """
    Turn on, off or toggle any entity that supports it (switch, light, fan, input_boolean, etc.).

    state: 'on' | 'off' | 'toggle' (default: toggle)
    """
    if state not in ("on", "off", "toggle"):
        raise ValueError("state must be: on, off, or toggle")
    service_map = {"on": "turn_on", "off": "turn_off", "toggle": "toggle"}
    with httpx.Client() as client:
        r = client.post(
            f"{HA_URL}/api/services/homeassistant/{service_map[state]}",
            headers=HEADERS,
            json={"entity_id": entity_id},
            timeout=10,
        )
        r.raise_for_status()
    return {"entity_id": entity_id, "state": state, "ok": True}
