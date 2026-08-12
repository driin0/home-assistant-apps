import httpx

from tools._base import mcp, HA_URL, HEADERS, _slug, _ws


@mcp.tool()
def list_automations(search: str = "") -> list:
    """
    List all automations with their state (on/off) and last triggered time.
    search: optional substring filter on automation name (case-insensitive)
    """
    with httpx.Client() as client:
        r = client.get(f"{HA_URL}/api/states", headers=HEADERS, timeout=15)
        r.raise_for_status()
        automations = []
        for s in r.json():
            if not s["entity_id"].startswith("automation."):
                continue
            name = s.get("attributes", {}).get("friendly_name", s["entity_id"])
            if search and search.lower() not in name.lower():
                continue
            automations.append({
                "entity_id": s["entity_id"],
                "name": name,
                "state": s["state"],
                "last_triggered": s.get("attributes", {}).get("last_triggered"),
            })
        return sorted(automations, key=lambda x: x["name"])


@mcp.tool()
def create_automation(
    name: str,
    trigger: list,
    action: list,
    condition: list = None,
    description: str = "",
    enabled: bool = True,
) -> dict:
    """
    Create or update an automation. The automation ID is derived from the name.

    trigger, condition and action must be valid HA trigger/condition/action objects.

    Example — turn on a light at sunset:
      name: "Turn on light at sunset"
      trigger: [{"platform": "sun", "event": "sunset"}]
      action: [{"service": "light.turn_on", "target": {"entity_id": "light.living_room"}}]

    Example — notify when door opens:
      name: "Notify door open"
      trigger: [{"platform": "state", "entity_id": "binary_sensor.front_door", "to": "on"}]
      action: [{"service": "notify.mobile_app_myphone", "data": {"message": "Door open!"}}]
    """
    automation_id = _slug(name)
    payload = {
        "alias": name,
        "description": description,
        "trigger": trigger,
        "condition": condition or [],
        "action": action,
        "mode": "single",
    }
    with httpx.Client() as client:
        r = client.post(
            f"{HA_URL}/api/config/automation/config/{automation_id}",
            headers=HEADERS,
            json=payload,
            timeout=15,
        )
        r.raise_for_status()
        if not enabled:
            client.post(
                f"{HA_URL}/api/services/automation/turn_off",
                headers=HEADERS,
                json={"entity_id": f"automation.{automation_id}"},
                timeout=10,
            )
        return {"automation_id": automation_id, "entity_id": f"automation.{automation_id}", "result": r.json()}


@mcp.tool()
def delete_automation(entity_id: str) -> dict:
    """
    Delete an automation by entity_id (e.g. 'automation.turn_on_light_at_sunset').
    Only works for automations managed via the HA UI editor.
    YAML-defined automations cannot be deleted via API.
    """
    automation_id = entity_id.removeprefix("automation.")
    with httpx.Client() as client:
        r = client.delete(
            f"{HA_URL}/api/config/automation/config/{automation_id}",
            headers=HEADERS,
            timeout=10,
        )
        if r.status_code == 404:
            return {
                "error": "not_found",
                "entity_id": entity_id,
                "detail": (
                    "This automation is defined in YAML and cannot be deleted via API. "
                    "Only UI-managed automations can be deleted with this tool."
                ),
            }
        r.raise_for_status()
        return {"deleted": entity_id, "status": r.status_code}


@mcp.tool()
def trigger_automation(entity_id: str) -> dict:
    """Manually trigger an automation regardless of its trigger conditions."""
    with httpx.Client() as client:
        r = client.post(
            f"{HA_URL}/api/services/automation/trigger",
            headers=HEADERS,
            json={"entity_id": entity_id},
            timeout=10,
        )
        r.raise_for_status()
        return {"triggered": entity_id}


@mcp.tool()
def toggle_automation(entity_id: str) -> dict:
    """Enable or disable an automation."""
    with httpx.Client() as client:
        r = client.post(
            f"{HA_URL}/api/services/automation/toggle",
            headers=HEADERS,
            json={"entity_id": entity_id},
            timeout=10,
        )
        r.raise_for_status()
        s = client.get(f"{HA_URL}/api/states/{entity_id}", headers=HEADERS, timeout=10)
        s.raise_for_status()
        return {"entity_id": entity_id, "new_state": s.json().get("state")}


@mcp.tool()
def get_automation(entity_id: str) -> dict:
    """
    Get the full config (triggers, conditions, actions) of an automation by entity_id.
    Resolves the numeric id from entity attributes and calls the HA config API directly,
    falling back to slug if no numeric id is available.
    """
    automation_slug = entity_id.removeprefix("automation.")
    with httpx.Client() as client:
        # Resolve numeric id from entity attributes (GUI automations use a timestamp id)
        automation_id = automation_slug
        state_r = client.get(f"{HA_URL}/api/states/{entity_id}", headers=HEADERS, timeout=10)
        if state_r.status_code == 200:
            numeric_id = state_r.json().get("attributes", {}).get("id")
            if numeric_id:
                automation_id = numeric_id

        r = client.get(
            f"{HA_URL}/api/config/automation/config/{automation_id}",
            headers=HEADERS,
            timeout=10,
        )
        if r.status_code != 404:
            r.raise_for_status()
            return r.json()

        # Fallback: try slug if numeric id didn't work
        if automation_id != automation_slug:
            r2 = client.get(
                f"{HA_URL}/api/config/automation/config/{automation_slug}",
                headers=HEADERS,
                timeout=10,
            )
            if r2.status_code != 404:
                r2.raise_for_status()
                return r2.json()

    return {
        "error": "not_found",
        "entity_id": entity_id,
        "detail": "Automation not found via HA config API.",
    }


@mcp.tool()
def get_automation_trace(entity_id: str, limit: int = 5) -> list:
    """
    Get the latest execution traces for an automation.
    Useful for debugging why an automation did or didn't trigger.

    entity_id: e.g. 'automation.living_room_lights'
    limit: number of recent traces to return (default 5)
    """
    result = _ws({
        "type": "automation/trace/list",
        "automation_id": entity_id.replace("automation.", ""),
    })
    traces = (result.get("result") or [])[:limit]
    return [
        {
            "run_id": t.get("run_id"),
            "state": t.get("state"),
            "timestamp": t.get("timestamp"),
            "trigger": t.get("trigger"),
            "error": t.get("error"),
            "script_execution": t.get("script_execution"),
        }
        for t in traces
    ]


@mcp.tool()
def list_blueprints(domain: str = "automation") -> list:
    """
    List available blueprints.

    domain: 'automation' (default) or 'script'
    """
    result = _ws({"type": "blueprint/list", "domain": domain})
    blueprints = result.get("result") or {}
    return [
        {
            "path": path,
            "name": data.get("metadata", {}).get("name", path),
            "description": data.get("metadata", {}).get("description", ""),
            "domain": data.get("metadata", {}).get("domain", domain),
            "input": list((data.get("metadata", {}).get("input") or {}).keys()),
        }
        for path, data in blueprints.items()
    ]


@mcp.tool()
def create_automation_from_blueprint(
    blueprint_path: str,
    alias: str,
    input_values: dict,
) -> dict:
    """
    Create an automation from a blueprint.

    blueprint_path: e.g. 'homeassistant/motion_trigger.yaml'
    alias: name for the new automation
    input_values: dict of blueprint input variables
    """
    result = _ws({
        "type": "config/automation/config/save",
        "config": {
            "alias": alias,
            "use_blueprint": {
                "path": blueprint_path,
                "input": input_values,
            },
        },
    })
    if not result.get("success", True):
        return {"error": result.get("error", {}).get("message", "unknown error")}
    return {"created": True, "alias": alias, "blueprint": blueprint_path}


@mcp.tool()
def list_device_triggers(device_id: str) -> list:
    """
    List all available automation triggers for a specific device.

    device_id: use list_devices() to find device IDs.

    Returns the triggers you can use in create_automation() — e.g. button presses,
    state changes, motion detection events, etc. specific to this device.
    Each trigger object can be used directly in the 'trigger' list of create_automation().
    """
    result = _ws({"type": "device_automation/trigger/list", "device_id": device_id})
    if not result.get("success", True):
        err = result.get("error", {})
        return [{"error": err.get("code", "unknown"), "detail": err.get("message", "")}]
    return result.get("result", [])


@mcp.tool()
def list_device_conditions(device_id: str) -> list:
    """
    List all available automation conditions for a specific device.

    device_id: use list_devices() to find device IDs.

    Returns conditions you can use in create_automation() — e.g. is device on/off,
    is a sensor above/below threshold, etc.
    Each condition object can be used directly in the 'condition' list of create_automation().
    """
    result = _ws({"type": "device_automation/condition/list", "device_id": device_id})
    if not result.get("success", True):
        err = result.get("error", {})
        return [{"error": err.get("code", "unknown"), "detail": err.get("message", "")}]
    return result.get("result", [])


@mcp.tool()
def list_device_actions(device_id: str) -> list:
    """
    List all available automation actions for a specific device.

    device_id: use list_devices() to find device IDs.

    Returns actions you can use in create_automation() — e.g. turn on/off, set brightness,
    lock/unlock, etc. specific to this device.
    Each action object can be used directly in the 'action' list of create_automation().
    """
    result = _ws({"type": "device_automation/action/list", "device_id": device_id})
    if not result.get("success", True):
        err = result.get("error", {})
        return [{"error": err.get("code", "unknown"), "detail": err.get("message", "")}]
    return result.get("result", [])


@mcp.tool()
def import_blueprint(url: str) -> dict:
    """
    Import a blueprint from a URL (GitHub, HA Community, etc.).

    url: direct URL to the blueprint YAML file.
    Examples:
      'https://raw.githubusercontent.com/user/repo/main/blueprints/automation/my_blueprint.yaml'
      'https://community.home-assistant.io/t/some-blueprint/123456'

    After importing, use list_blueprints() to see it and
    create_automation_from_blueprint() to use it.
    """
    result = _ws({"type": "blueprint/import", "url": url})
    if not result.get("success", True):
        err = result.get("error", {})
        return {"error": err.get("code", "unknown"), "detail": err.get("message", str(err))}
    data = result.get("result") or {}
    return {
        "imported": True,
        "url": url,
        "path": data.get("suggested_filename") or data.get("path", ""),
        "name": data.get("blueprint", {}).get("metadata", {}).get("name", ""),
        "domain": data.get("blueprint", {}).get("metadata", {}).get("domain", ""),
    }


@mcp.tool()
def list_schedules() -> list:
    """
    List all schedules from the Scheduler integration (HACS custom component).
    Returns an empty list with a note if the integration is not installed.
    """
    r = _ws({"type": "scheduler/items"})
    # If scheduler is not installed, HA returns an error result
    if not r.get("success", True) or "error" in r:
        return [{
            "error": "scheduler_not_available",
            "detail": "The Scheduler custom integration is not installed or not loaded.",
        }]
    items = r.get("result", [])
    result = []
    for item in items:
        result.append({
            "schedule_id": item.get("schedule_id"),
            "entity_id": item.get("entity_id"),
            "name": item.get("name", ""),
            "enabled": item.get("enabled", True),
            "next_trigger": item.get("next_trigger"),
            "timeslots": item.get("timeslots", []),
            "actions": item.get("actions", []),
        })
    return sorted(result, key=lambda x: x.get("name", ""))
