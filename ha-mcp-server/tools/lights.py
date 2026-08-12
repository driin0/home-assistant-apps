import httpx

from tools._base import mcp, HA_URL, HEADERS


@mcp.tool()
def list_lights(area_id: str = "", search: str = "", state: str = "") -> list:
    """
    List all light entities with their current state, brightness and color.

    area_id: filter by area_id (use list_areas() to find IDs)
    search:  optional substring filter on entity_id or friendly name (case-insensitive)
    state:   filter by exact state — 'on', 'off', 'unavailable'
    """
    with httpx.Client() as client:
        r = client.get(f"{HA_URL}/api/states", headers=HEADERS, timeout=15)
        r.raise_for_status()
    lights = []
    for s in r.json():
        if not s["entity_id"].startswith("light."):
            continue
        attrs = s.get("attributes", {})
        if area_id and attrs.get("area_id") != area_id:
            continue
        if state and s["state"] != state:
            continue
        name = attrs.get("friendly_name", s["entity_id"])
        if search and search.lower() not in s["entity_id"].lower() and search.lower() not in name.lower():
            continue
        lights.append({
            "entity_id": s["entity_id"],
            "name": name,
            "state": s["state"],
            "brightness_pct": round(attrs["brightness"] / 2.55) if attrs.get("brightness") is not None else None,
            "color_temp_k": attrs.get("color_temp_kelvin"),
            "rgb_color": attrs.get("rgb_color"),
            "color_mode": attrs.get("color_mode"),
            "supported_color_modes": attrs.get("supported_color_modes", []),
        })
    return sorted(lights, key=lambda x: x["name"])


@mcp.tool()
def set_light(
    entity_id: str,
    state: str = "",
    brightness_pct: int = None,
    color_temp_k: int = None,
    rgb_color: list = None,
    effect: str = "",
    transition: int = None,
) -> dict:
    """
    Control a light entity.

    state: 'on' | 'off' | 'toggle'
    brightness_pct: 0–100
    color_temp_k: color temperature in Kelvin (e.g. 2700 warm, 4000 neutral, 6500 cool)
    rgb_color: [R, G, B] list, e.g. [255, 100, 0]
    effect: named effect (e.g. 'Night', 'Day', 'Candle', 'Twinkle') — see entity's effect_list
    transition: fade duration in seconds
    """
    with httpx.Client() as client:
        if state == "off":
            data: dict = {"entity_id": entity_id}
            if transition is not None:
                data["transition"] = transition
            r = client.post(f"{HA_URL}/api/services/light/turn_off", headers=HEADERS, json=data, timeout=10)
        elif state == "toggle":
            r = client.post(f"{HA_URL}/api/services/light/toggle", headers=HEADERS,
                            json={"entity_id": entity_id}, timeout=10)
        else:
            data = {"entity_id": entity_id}
            if brightness_pct is not None:
                data["brightness_pct"] = brightness_pct
            if color_temp_k is not None:
                data["color_temp_kelvin"] = color_temp_k
            if rgb_color is not None:
                data["rgb_color"] = rgb_color
            if effect:
                data["effect"] = effect
            if transition is not None:
                data["transition"] = transition
            r = client.post(f"{HA_URL}/api/services/light/turn_on", headers=HEADERS, json=data, timeout=10)
        r.raise_for_status()
    return {"entity_id": entity_id, "state": state or "on", "ok": True}
