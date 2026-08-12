import httpx

from tools._base import mcp, HA_URL, HEADERS


@mcp.tool()
def list_climate() -> list:
    """List all climate entities (AC, heaters, etc.) with current state."""
    with httpx.Client() as client:
        r = client.get(f"{HA_URL}/api/states", headers=HEADERS, timeout=15)
        r.raise_for_status()
        result = []
        for s in r.json():
            if not s["entity_id"].startswith("climate."):
                continue
            attrs = s.get("attributes", {})
            result.append({
                "entity_id": s["entity_id"],
                "name": attrs.get("friendly_name", s["entity_id"]),
                "state": s["state"],
                "current_temperature": attrs.get("current_temperature"),
                "temperature": attrs.get("temperature"),
                "hvac_modes": attrs.get("hvac_modes", []),
                "fan_mode": attrs.get("fan_mode"),
                "fan_modes": attrs.get("fan_modes", []),
                "swing_mode": attrs.get("swing_mode"),
                "swing_modes": attrs.get("swing_modes", []),
            })
        return sorted(result, key=lambda x: x["name"])


@mcp.tool()
def set_climate(
    entity_id: str,
    hvac_mode: str = "",
    temperature: float = None,
    fan_mode: str = "",
    swing_mode: str = "",
) -> dict:
    """
    Control a climate entity.

    hvac_mode:   'off', 'cool', 'heat', 'dry', 'fan_only', 'auto'
    temperature: target temperature in °C
    fan_mode:    'auto', 'low', 'medium', 'high', etc. (depends on device)
    swing_mode:  'off', 'vertical', 'horizontal', 'both', etc. (depends on device)
    """
    with httpx.Client() as client:
        applied = {}
        if hvac_mode:
            r = client.post(f"{HA_URL}/api/services/climate/set_hvac_mode",
                            headers=HEADERS,
                            json={"entity_id": entity_id, "hvac_mode": hvac_mode}, timeout=10)
            r.raise_for_status()
            applied["hvac_mode"] = hvac_mode
        if temperature is not None:
            r = client.post(f"{HA_URL}/api/services/climate/set_temperature",
                            headers=HEADERS,
                            json={"entity_id": entity_id, "temperature": temperature}, timeout=10)
            r.raise_for_status()
            applied["temperature"] = temperature
        if fan_mode:
            r = client.post(f"{HA_URL}/api/services/climate/set_fan_mode",
                            headers=HEADERS,
                            json={"entity_id": entity_id, "fan_mode": fan_mode}, timeout=10)
            r.raise_for_status()
            applied["fan_mode"] = fan_mode
        if swing_mode:
            r = client.post(f"{HA_URL}/api/services/climate/set_swing_mode",
                            headers=HEADERS,
                            json={"entity_id": entity_id, "swing_mode": swing_mode}, timeout=10)
            r.raise_for_status()
            applied["swing_mode"] = swing_mode
        return {"entity_id": entity_id, "applied": applied, "ok": True}
