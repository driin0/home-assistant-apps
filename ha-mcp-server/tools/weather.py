import httpx

from tools._base import mcp, HA_URL, HEADERS, _ws


@mcp.tool()
def get_weather(entity_id: str = "", forecast_type: str = "hourly") -> dict:
    """
    Get current weather conditions and forecast.
    If entity_id is empty, uses the first available weather entity.

    forecast_type: hourly | daily | twice_daily
    """
    with httpx.Client() as client:
        r = client.get(f"{HA_URL}/api/states", headers=HEADERS, timeout=15)
        r.raise_for_status()
    all_states = r.json()
    if entity_id:
        states = [s for s in all_states if s["entity_id"] == entity_id]
    else:
        states = [s for s in all_states if s["entity_id"].startswith("weather.")]
    if not states:
        return {"error": "No weather entity found"}
    s = states[0]
    eid = s["entity_id"]
    attrs = s.get("attributes", {})

    # HA 2024.3+: forecasts via WS call_service with return_response
    forecast = []
    result = _ws({
        "type": "call_service",
        "domain": "weather",
        "service": "get_forecasts",
        "service_data": {"entity_id": eid, "type": forecast_type},
        "return_response": True,
    })
    response = (result.get("result") or {}).get("response", {})
    forecast = response.get(eid, {}).get("forecast", [])[:12]

    # Fallback to legacy attribute (pre-2024.3)
    if not forecast:
        forecast = attrs.get("forecast", [])[:12]

    return {
        "entity_id": eid,
        "name": attrs.get("friendly_name", eid),
        "condition": s["state"],
        "temperature": attrs.get("temperature"),
        "temperature_unit": attrs.get("temperature_unit"),
        "humidity": attrs.get("humidity"),
        "wind_speed": attrs.get("wind_speed"),
        "wind_bearing": attrs.get("wind_bearing"),
        "pressure": attrs.get("pressure"),
        "visibility": attrs.get("visibility"),
        "forecast_type": forecast_type,
        "forecast": forecast,
    }
