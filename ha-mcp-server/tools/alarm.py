import httpx

from tools._base import mcp, HA_URL, HEADERS


@mcp.tool()
def alarm_control(entity_id: str, command: str, code: str = "") -> dict:
    """
    Arm or disarm an alarm control panel (Alarmo and others).

    command: disarm | arm_home | arm_away | arm_night | arm_vacation | arm_custom_bypass
    code: optional alarm code (required if the panel is configured to need one)

    ⚠️ SAFETY: This controls a physical alarm system. Always confirm the entity and
    command with the user before executing.
    """
    valid = {"disarm", "arm_home", "arm_away", "arm_night", "arm_vacation", "arm_custom_bypass"}
    if command not in valid:
        return {"error": f"Invalid command. Use one of: {sorted(valid)}"}
    service = f"alarm_{command}"  # HA service names: alarm_disarm, alarm_arm_home, etc.
    data: dict = {"entity_id": entity_id}
    if code:
        data["code"] = code
    with httpx.Client() as client:
        r = client.post(
            f"{HA_URL}/api/services/alarm_control_panel/{service}",
            headers=HEADERS,
            json=data,
            timeout=15,
        )
        r.raise_for_status()
    return {"entity_id": entity_id, "command": command, "ok": True}


@mcp.tool()
def get_alarm_state() -> list:
    """Get the current state of all alarm control panels (Alarmo and others)."""
    with httpx.Client() as client:
        r = client.get(f"{HA_URL}/api/states", headers=HEADERS, timeout=15)
        r.raise_for_status()
        alarms = []
        for s in r.json():
            if not s["entity_id"].startswith("alarm_control_panel."):
                continue
            attrs = s.get("attributes", {})
            alarms.append({
                "entity_id": s["entity_id"],
                "name": attrs.get("friendly_name", s["entity_id"]),
                "state": s["state"],
                "code_format": attrs.get("code_format"),
                "changed_by": attrs.get("changed_by"),
                "open_sensors": attrs.get("open_sensors", {}),
                "bypassed_sensors": attrs.get("bypassed_sensors", []),
                "last_changed": s.get("last_changed", ""),
            })
        return sorted(alarms, key=lambda x: x["name"])
