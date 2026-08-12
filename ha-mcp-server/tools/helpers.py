import httpx

from tools._base import mcp, HA_URL, HEADERS, HELPER_DOMAINS, _slug, _ws


@mcp.tool()
def list_helpers(domain: str = "") -> list:
    """
    List helpers, optionally filtered by domain.

    domain: leave empty for all, or one of:
      input_boolean, input_number, input_text, input_select,
      input_datetime, counter, timer, input_button
    """
    with httpx.Client() as client:
        r = client.get(f"{HA_URL}/api/states", headers=HEADERS, timeout=15)
        r.raise_for_status()
        helpers = []
        for s in r.json():
            d = s["entity_id"].split(".")[0]
            if d not in HELPER_DOMAINS:
                continue
            if domain and d != domain:
                continue
            helpers.append({
                "entity_id": s["entity_id"],
                "domain": d,
                "name": s.get("attributes", {}).get("friendly_name", s["entity_id"]),
                "state": s["state"],
                "attributes": {
                    k: v for k, v in s.get("attributes", {}).items()
                    if k not in ("friendly_name", "icon", "editable")
                },
            })
        return sorted(helpers, key=lambda x: (x["domain"], x["name"]))


@mcp.tool()
def set_helper(entity_id: str, value: str) -> dict:
    """
    Set the value of a helper entity.

    - input_boolean: value = 'on' or 'off'
    - input_number:  value = numeric string (e.g. '42')
    - input_text:    value = any string
    - input_select:  value = one of the allowed options
    - input_datetime: value = 'YYYY-MM-DD HH:MM:SS' or 'HH:MM:SS' or 'YYYY-MM-DD'
    - counter:       value = 'increment', 'decrement', or 'reset'
    - timer:         value = 'start', 'pause', 'cancel', or 'finish'
    """
    domain = entity_id.split(".")[0]
    with httpx.Client() as client:
        if domain == "input_boolean":
            svc = "turn_on" if value == "on" else "turn_off"
            r = client.post(f"{HA_URL}/api/services/input_boolean/{svc}",
                            headers=HEADERS, json={"entity_id": entity_id}, timeout=10)
        elif domain == "input_number":
            r = client.post(f"{HA_URL}/api/services/input_number/set_value",
                            headers=HEADERS,
                            json={"entity_id": entity_id, "value": float(value)}, timeout=10)
        elif domain == "input_text":
            r = client.post(f"{HA_URL}/api/services/input_text/set_value",
                            headers=HEADERS,
                            json={"entity_id": entity_id, "value": value}, timeout=10)
        elif domain == "input_select":
            r = client.post(f"{HA_URL}/api/services/input_select/select_option",
                            headers=HEADERS,
                            json={"entity_id": entity_id, "option": value}, timeout=10)
        elif domain == "input_datetime":
            r = client.post(f"{HA_URL}/api/services/input_datetime/set_datetime",
                            headers=HEADERS,
                            json={"entity_id": entity_id, "datetime": value}, timeout=10)
        elif domain == "counter":
            svc = value if value in ("increment", "decrement", "reset") else "increment"
            r = client.post(f"{HA_URL}/api/services/counter/{svc}",
                            headers=HEADERS, json={"entity_id": entity_id}, timeout=10)
        elif domain == "timer":
            svc = value if value in ("start", "pause", "cancel", "finish") else "start"
            r = client.post(f"{HA_URL}/api/services/timer/{svc}",
                            headers=HEADERS, json={"entity_id": entity_id}, timeout=10)
        else:
            return {"error": f"Unsupported helper domain: {domain}"}
        r.raise_for_status()
        return {"entity_id": entity_id, "value": value, "ok": True}


@mcp.tool()
def create_helper(
    domain: str,
    name: str,
    config: dict = None,
) -> dict:
    """
    Create a new helper entity.

    domain: one of input_boolean, input_number, input_text,
            input_select, input_datetime, counter, timer, input_button

    config: optional domain-specific fields. Examples:

    input_boolean:
      {}  (no extra config needed)

    input_number:
      {"min": 0, "max": 100, "step": 1, "unit_of_measurement": "%"}

    input_text:
      {"min": 0, "max": 100}

    input_select:
      {"options": ["Option A", "Option B", "Option C"]}

    input_datetime:
      {"has_date": true, "has_time": true}

    counter:
      {"initial": 0, "step": 1, "minimum": 0, "maximum": 100, "restore": true}

    timer:
      {"duration": "00:05:00", "restore": false}

    input_button:
      {}  (no extra config needed)
    """
    supported = {
        "input_boolean", "input_number", "input_text", "input_select",
        "input_datetime", "counter", "timer", "input_button",
    }
    if domain not in supported:
        return {"error": f"Unsupported domain: {domain}. Use one of: {sorted(supported)}"}
    # Helper "storage" collections are created over the WebSocket API
    # ({domain}/create) — exactly like the GUI helper editor. There is no REST
    # config endpoint for these, so an httpx POST returns 404.
    res = _ws({"type": f"{domain}/create", "name": name, **(config or {})})
    if not res.get("success"):
        return {"error": "WebSocket create failed", "domain": domain,
                "name": name, "detail": res.get("error")}
    item = res.get("result") or {}
    helper_id = item.get("id", _slug(name))
    return {"helper_id": helper_id, "entity_id": f"{domain}.{helper_id}", "result": item}


@mcp.tool()
def delete_helper(entity_id: str) -> dict:
    """
    Delete a helper entity by entity_id.
    Supported: input_boolean, input_number, input_text, input_select,
               input_datetime, counter, timer, input_button.
    """
    domain = entity_id.split(".")[0]
    supported = {
        "input_boolean", "input_number", "input_text", "input_select",
        "input_datetime", "counter", "timer", "input_button",
    }
    if domain not in supported:
        return {"error": f"Cannot delete domain: {domain}"}
    helper_id = entity_id.split(".", 1)[1]
    # Storage-collection delete also goes over the WebSocket API.
    res = _ws({"type": f"{domain}/delete", f"{domain}_id": helper_id})
    if not res.get("success"):
        return {"error": "WebSocket delete failed", "entity_id": entity_id,
                "detail": res.get("error")}
    return {"deleted": entity_id, "ok": True}


@mcp.tool()
def create_template_sensor(
    name: str,
    state_template: str,
    unit_of_measurement: str = "",
    icon: str = "",
    device_class: str = "",
    state_class: str = "",
) -> dict:
    """
    Create a template sensor helper in Home Assistant via the config flow.

    state_template: Jinja2 template for the sensor value.

    Examples:
      Count local light groups only, excluding entities mirrored from other
      instances (adjust the pattern to your own remote prefixes):
        state_template: >
          {{ states.light
             | selectattr('attributes.entity_id', 'defined')
             | rejectattr('entity_id', 'search', 'annex|workshop')
             | list | count }}

      Current temperature from a sensor:
        state_template: "{{ states('sensor.living_room_temperature') }}"
    """
    with httpx.Client() as client:
        # Step 1: start the template config flow
        r1 = client.post(
            f"{HA_URL}/api/config/config_entries/flow",
            headers=HEADERS,
            json={"handler": "template"},
            timeout=15,
        )
        r1.raise_for_status()
        flow = r1.json()
        flow_id = flow["flow_id"]

        # Step 2: select sensor as template type (template flow starts with a menu)
        r2 = client.post(
            f"{HA_URL}/api/config/config_entries/flow/{flow_id}",
            headers=HEADERS,
            json={"next_step_id": "sensor"},
            timeout=15,
        )
        r2.raise_for_status()
        form_schema = r2.json()

        # Step 3: submit sensor config — only include fields present in the schema
        schema_keys = {f["name"] for f in form_schema.get("data_schema", [])}
        candidate: dict = {
            "name": name,
            "state": state_template,
            "unit_of_measurement": unit_of_measurement,
            "icon": icon,
            "device_class": device_class,
            "state_class": state_class,
        }
        payload = {k: v for k, v in candidate.items() if v and (not schema_keys or k in schema_keys)}

        r3 = client.post(
            f"{HA_URL}/api/config/config_entries/flow/{flow_id}",
            headers=HEADERS,
            json=payload,
            timeout=15,
        )
        if r3.status_code == 400:
            return {"error": "400 on form submit", "schema": form_schema, "payload_sent": payload}
        r3.raise_for_status()
        result = r3.json()
        entry_id = result.get("result", {}).get("entry_id", "")

        response: dict = {"entry_id": entry_id, "name": name, "result": result}
        if icon and entry_id:
            entity_id = f"sensor.{_slug(name)}"
            try:
                ws_result = _ws({
                    "type": "config/entity_registry/update",
                    "entity_id": entity_id,
                    "icon": icon,
                })
                response["icon_set"] = ws_result.get("success", False)
                if not ws_result.get("success"):
                    response["icon_error"] = ws_result
            except Exception as exc:
                response["icon_error"] = str(exc)
        return response


@mcp.tool()
def delete_template_sensor(entry_id: str) -> dict:
    """
    Delete a template sensor config entry by entry_id.
    Use the entry_id returned by create_template_sensor.
    """
    with httpx.Client() as client:
        r = client.delete(
            f"{HA_URL}/api/config/config_entries/entry/{entry_id}",
            headers=HEADERS,
            timeout=10,
        )
        r.raise_for_status()
        return {"deleted": entry_id, "status": r.status_code}


@mcp.tool()
def set_number(entity_id: str, value: float) -> dict:
    """
    Set the value of a number or input_number entity.

    entity_id: e.g. 'number.volume' or 'input_number.timer_minutes'
    value: numeric value within the entity's min/max range
    """
    domain = entity_id.split(".")[0]
    if domain not in ("number", "input_number"):
        raise ValueError("entity_id must be a number.* or input_number.* entity")
    with httpx.Client() as client:
        r = client.post(
            f"{HA_URL}/api/services/{domain}/set_value",
            headers=HEADERS,
            json={"entity_id": entity_id, "value": value},
            timeout=10,
        )
        r.raise_for_status()
    return {"entity_id": entity_id, "value": value, "ok": True}


@mcp.tool()
def set_select(entity_id: str, option: str) -> dict:
    """
    Set the selected option of a select or input_select entity.

    entity_id: e.g. 'select.fan_mode' or 'input_select.scene'
    option: one of the available options for this entity
    """
    domain = entity_id.split(".")[0]
    if domain not in ("select", "input_select"):
        raise ValueError("entity_id must be a select.* or input_select.* entity")
    service = "select_option" if domain == "input_select" else "select_option"
    with httpx.Client() as client:
        r = client.post(
            f"{HA_URL}/api/services/{domain}/{service}",
            headers=HEADERS,
            json={"entity_id": entity_id, "option": option},
            timeout=10,
        )
        r.raise_for_status()
    return {"entity_id": entity_id, "option": option, "ok": True}


@mcp.tool()
def set_text(entity_id: str, value: str) -> dict:
    """
    Set the value of a text or input_text entity.

    entity_id: e.g. 'input_text.message'
    value: string value
    """
    domain = entity_id.split(".")[0]
    if domain not in ("text", "input_text"):
        raise ValueError("entity_id must be a text.* or input_text.* entity")
    with httpx.Client() as client:
        r = client.post(
            f"{HA_URL}/api/services/{domain}/set_value",
            headers=HEADERS,
            json={"entity_id": entity_id, "value": value},
            timeout=10,
        )
        r.raise_for_status()
    return {"entity_id": entity_id, "value": value, "ok": True}


@mcp.tool()
def timer_control(entity_id: str, command: str, duration: str = "") -> dict:
    """
    Control a timer entity.

    command: 'start' | 'pause' | 'cancel' | 'finish'
    duration: optional override duration in HH:MM:SS format (only for 'start')
    """
    if command not in ("start", "pause", "cancel", "finish"):
        raise ValueError("command must be: start, pause, cancel, or finish")
    data: dict = {"entity_id": entity_id}
    if command == "start" and duration:
        data["duration"] = duration
    with httpx.Client() as client:
        r = client.post(
            f"{HA_URL}/api/services/timer/{command}",
            headers=HEADERS,
            json=data,
            timeout=10,
        )
        r.raise_for_status()
    return {"entity_id": entity_id, "command": command, "ok": True}


@mcp.tool()
def counter_control(entity_id: str, command: str) -> dict:
    """
    Control a counter entity.

    command: 'increment' | 'decrement' | 'reset'
    """
    if command not in ("increment", "decrement", "reset"):
        raise ValueError("command must be: increment, decrement, or reset")
    with httpx.Client() as client:
        r = client.post(
            f"{HA_URL}/api/services/counter/{command}",
            headers=HEADERS,
            json={"entity_id": entity_id},
            timeout=10,
        )
        r.raise_for_status()
    return {"entity_id": entity_id, "command": command, "ok": True}
