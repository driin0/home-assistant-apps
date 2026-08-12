import httpx

from tools._base import mcp, HA_URL, HEADERS


@mcp.tool()
def list_alerts() -> list:
    """
    List all alert entities (alert.*) with their current state.

    Alert entities fire repeatedly (with configurable intervals) while a condition is active,
    until acknowledged. Useful for monitoring critical conditions like gas leaks, flooding, etc.

    Returns: [{entity_id, name, state, last_changed, attributes}]
    States: 'idle' (condition inactive), 'on' (firing), 'off' (acknowledged/snoozed)
    """
    with httpx.Client() as client:
        r = client.get(f"{HA_URL}/api/states", headers=HEADERS, timeout=15)
        r.raise_for_status()
    alerts = []
    for s in r.json():
        if not s["entity_id"].startswith("alert."):
            continue
        attrs = s.get("attributes", {})
        alerts.append({
            "entity_id": s["entity_id"],
            "name": attrs.get("friendly_name", s["entity_id"]),
            "state": s["state"],
            "last_changed": s.get("last_changed", "")[:19],
            "notification_frequency_minutes": attrs.get("notification_frequency"),
            "data": attrs.get("data", {}),
        })
    return sorted(alerts, key=lambda x: x["name"])


@mcp.tool()
def acknowledge_alert(entity_id: str) -> dict:
    """
    Acknowledge a firing alert to stop repeated notifications.

    entity_id: alert entity to acknowledge (e.g. 'alert.gas_leak')
    Use list_alerts() to find active alerts.

    Acknowledged alerts will resume firing if the condition is still active
    after the configured notification interval.
    """
    with httpx.Client() as client:
        r = client.post(
            f"{HA_URL}/api/services/alert/acknowledge",
            headers=HEADERS,
            json={"entity_id": entity_id},
            timeout=10,
        )
        r.raise_for_status()
    return {"acknowledged": entity_id, "success": True}


@mcp.tool()
def toggle_alert(entity_id: str, action: str = "toggle") -> dict:
    """
    Turn an alert on, off, or toggle it.

    entity_id: alert entity (e.g. 'alert.gas_leak')
    action: 'on' | 'off' | 'toggle' (default: 'toggle')
            'off' silences the alert (same as acknowledge)
            'on'  re-enables a silenced alert
    """
    service = {"on": "turn_on", "off": "turn_off", "toggle": "toggle"}.get(action, "toggle")
    with httpx.Client() as client:
        r = client.post(
            f"{HA_URL}/api/services/alert/{service}",
            headers=HEADERS,
            json={"entity_id": entity_id},
            timeout=10,
        )
        r.raise_for_status()
    return {"entity_id": entity_id, "action": action, "success": True}
