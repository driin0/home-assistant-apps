import httpx
from datetime import datetime, timedelta, timezone

from tools._base import mcp, HA_URL, HEADERS, default_language, _ws, _ws_multi


@mcp.tool()
def get_config() -> dict:
    """Get Home Assistant info: version, location, timezone, enabled components."""
    with httpx.Client() as client:
        r = client.get(f"{HA_URL}/api/config", headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json()
        return {
            "version": data.get("version"),
            "location_name": data.get("location_name"),
            "time_zone": data.get("time_zone"),
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "components": sorted(data.get("components", [])),
        }


@mcp.tool()
def get_entity(entity_id: str) -> dict:
    """Get the current state and attributes of a single entity by entity_id."""
    with httpx.Client() as client:
        r = client.get(f"{HA_URL}/api/states/{entity_id}", headers=HEADERS, timeout=10)
        r.raise_for_status()
        s = r.json()
        return {
            "entity_id": s["entity_id"],
            "state": s["state"],
            "attributes": s.get("attributes", {}),
            "last_changed": s.get("last_changed", ""),
            "last_updated": s.get("last_updated", ""),
        }


@mcp.tool()
def get_states_by_domain(domain: str) -> list:
    """
    Get all entity states for a given domain.
    Examples: 'light', 'switch', 'sensor', 'binary_sensor', 'climate',
              'media_player', 'automation', 'script', 'scene', 'person'
    """
    with httpx.Client() as client:
        r = client.get(f"{HA_URL}/api/states", headers=HEADERS, timeout=15)
        r.raise_for_status()
        return [
            {
                "entity_id": s["entity_id"],
                "name": s.get("attributes", {}).get("friendly_name", ""),
                "state": s["state"],
                "attributes": s.get("attributes", {}),
                "last_changed": s.get("last_changed", ""),
            }
            for s in r.json()
            if s["entity_id"].startswith(f"{domain}.")
        ]


@mcp.tool()
def get_history(entity_id: str, hours: int = 24) -> list:
    """Get state history for an entity over the last N hours (default 24)."""
    start = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    with httpx.Client() as client:
        r = client.get(
            f"{HA_URL}/api/history/period/{start}",
            headers=HEADERS,
            params={"filter_entity_id": entity_id, "minimal_response": "true"},
            timeout=20,
        )
        r.raise_for_status()
        result = r.json()
        return result[0] if result else []


@mcp.tool()
def get_logbook(hours: int = 6, entity_id: str = "") -> list:
    """
    Get the logbook (events and state changes) for the last N hours (default 6).
    Optionally filter by entity_id to reduce output size.
    """
    start = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    params = {}
    if entity_id:
        params["entity"] = entity_id
    with httpx.Client() as client:
        r = client.get(
            f"{HA_URL}/api/logbook/{start}",
            headers=HEADERS,
            params=params,
            timeout=20,
        )
        r.raise_for_status()
        entries = r.json()
        return [
            {
                "when": e.get("when", "")[:16],
                "domain": e.get("domain", ""),
                "name": e.get("name", ""),
                "message": e.get("message", ""),
                "entity_id": e.get("entity_id", ""),
            }
            for e in entries
            if e.get("domain")
        ]


@mcp.tool()
def get_error_log() -> str:
    """
    Get the Home Assistant error log.

    Not every installation serves /api/error_log — it is absent on recent cores
    and when the log is written elsewhere — so a missing endpoint is reported as
    a message rather than raised.
    """
    with httpx.Client() as client:
        r = client.get(f"{HA_URL}/api/error_log", headers=HEADERS, timeout=10)
        if r.status_code == 404:
            return (
                "error_log_not_available: this Home Assistant instance does not serve "
                "/api/error_log. Read the log from Settings -> System -> Logs, or use "
                "get_logbook() for entity activity."
            )
        r.raise_for_status()
        return r.text


@mcp.tool()
def list_services(domain: str = "") -> dict:
    """
    List available HA services, optionally filtered by domain.
    Examples: domain='light', 'notify', 'automation', 'input_boolean'
    """
    with httpx.Client() as client:
        r = client.get(f"{HA_URL}/api/services", headers=HEADERS, timeout=15)
        r.raise_for_status()
        services = r.json()
        if domain:
            services = [s for s in services if s.get("domain") == domain]
        return {
            s["domain"]: list(s.get("services", {}).keys())
            for s in services
        }


@mcp.tool()
def get_sun() -> dict:
    """
    Get current sun position and next rise/set times.
    Returns elevation, azimuth, phase (rising/setting), and next_rising/next_setting timestamps.
    Useful for understanding the current light conditions and planning time-based automations.
    """
    with httpx.Client() as client:
        r = client.get(f"{HA_URL}/api/states/sun.sun", headers=HEADERS, timeout=10)
        r.raise_for_status()
        s = r.json()
        attrs = s.get("attributes", {})
        return {
            "state": s["state"],  # "above_horizon" or "below_horizon"
            "elevation": attrs.get("elevation"),
            "azimuth": attrs.get("azimuth"),
            "rising": attrs.get("rising"),
            "next_rising": attrs.get("next_rising", "")[:19],
            "next_setting": attrs.get("next_setting", "")[:19],
            "next_dawn": attrs.get("next_dawn", "")[:19],
            "next_dusk": attrs.get("next_dusk", "")[:19],
            "next_midnight": attrs.get("next_midnight", "")[:19],
            "next_noon": attrs.get("next_noon", "")[:19],
        }


@mcp.tool()
def process_conversation(text: str, language: str = "") -> dict:
    """
    Process a natural language command through Home Assistant's conversation agent.

    text: natural language command, e.g. "turn on the living room lights"
    language: language code; defaults to the language configured in Home Assistant

    The response contains the agent's reply and any actions taken.
    """
    language = language or default_language()
    with httpx.Client() as client:
        r = client.post(
            f"{HA_URL}/api/conversation/process",
            headers=HEADERS,
            json={"text": text, "language": language},
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        response = data.get("response", {})
        return {
            "speech": response.get("speech", {}).get("plain", {}).get("speech", ""),
            "response_type": response.get("response_type", ""),
            "language": data.get("language", language),
        }


@mcp.tool()
def trigger_webhook(webhook_id: str, data: dict = None, method: str = "post") -> dict:
    """
    Trigger a Home Assistant webhook by its webhook_id.

    webhook_id: the ID as configured in the automation/script trigger
    data: optional JSON payload to send with the webhook
    method: 'post' (default) or 'get'

    Note: the webhook must be configured in HA to allow external access.
    """
    with httpx.Client() as client:
        url = f"{HA_URL}/api/webhook/{webhook_id}"
        if method.lower() == "get":
            r = client.get(url, headers=HEADERS, params=data or {}, timeout=10)
        else:
            r = client.post(url, headers=HEADERS, json=data or {}, timeout=10)
        # Webhooks return 200 with empty body or 200 with JSON — both are valid
        return {"webhook_id": webhook_id, "status_code": r.status_code, "triggered": r.status_code < 300}


@mcp.tool()
def render_template(template: str) -> str:
    """
    Render a Jinja2 template using Home Assistant's template engine and return the result.

    Useful for complex queries on HA data, calculated values, or testing templates before
    using them in automations.

    Examples:
      "{{ states('sensor.living_room_temperature') }}"
      "{{ states.light | selectattr('state','eq','on') | list | count }} lights on"
      "{{ now().strftime('%H:%M') }}"
    """
    with httpx.Client() as client:
        r = client.post(
            f"{HA_URL}/api/template",
            headers=HEADERS,
            json={"template": template},
            timeout=15,
        )
        r.raise_for_status()
        return r.text


@mcp.tool()
def fire_event(event_type: str, event_data: dict = None) -> dict:
    """
    Fire a custom event on the Home Assistant event bus.

    event_type: the event name, e.g. 'my_custom_event' or 'mobile_app_notification_action'
    event_data: optional dict of event data

    Useful for triggering automations that listen on custom events, or for testing
    event-based automations.
    """
    with httpx.Client() as client:
        r = client.post(
            f"{HA_URL}/api/events/{event_type}",
            headers=HEADERS,
            json=event_data or {},
            timeout=10,
        )
        r.raise_for_status()
    return {"fired": True, "event_type": event_type, "event_data": event_data or {}}


@mcp.tool()
def list_entities_by_integration(integration: str, search: str = "", limit: int = 0) -> list:
    """
    List all entities belonging to a specific integration (platform).

    integration: integration domain, e.g. 'remote_homeassistant', 'shelly', 'yeelight', 'mqtt'
    search: optional substring filter on entity_id or name (case-insensitive)
    limit: max results to return (0 = no limit)

    Returns entity_id, name, area_id for each matching entity.
    Useful to discover which entities come from a specific integration or remote HA instance.
    """
    result = _ws({"type": "config/entity_registry/list"})
    entities = result.get("result", [])
    out = []
    for e in entities:
        if e.get("platform") != integration:
            continue
        name = e.get("name") or e.get("original_name", "")
        if search and search.lower() not in e["entity_id"].lower() and search.lower() not in name.lower():
            continue
        out.append({
            "entity_id": e["entity_id"],
            "name": name,
            "platform": e.get("platform"),
            "area_id": e.get("area_id"),
            "disabled": e.get("disabled_by") is not None,
        })
        if limit and len(out) >= limit:
            break
    return out


@mcp.tool()
def get_live_context() -> dict:
    """
    Return a concise snapshot of the current Home Assistant state.

    Includes: who's home, lights on, alarm state, active media players,
    open covers, climate summary, and any active alerts/warnings.
    Useful as a quick situational overview before issuing commands.
    """
    with httpx.Client() as client:
        r = client.get(f"{HA_URL}/api/states", headers=HEADERS, timeout=15)
        r.raise_for_status()
        all_states = r.json()

    def by_domain(domain):
        return [s for s in all_states if s["entity_id"].startswith(f"{domain}.")]

    # Persons
    persons = [
        {"name": s["attributes"].get("friendly_name", s["entity_id"]), "state": s["state"]}
        for s in by_domain("person")
    ]

    # Lights on
    lights_on = [
        s["attributes"].get("friendly_name", s["entity_id"])
        for s in by_domain("light") if s["state"] == "on"
    ]

    # Alarm
    alarms = [
        {"entity_id": s["entity_id"], "state": s["state"]}
        for s in by_domain("alarm_control_panel")
    ]

    # Active media players
    media_active = [
        {
            "name": s["attributes"].get("friendly_name", s["entity_id"]),
            "state": s["state"],
            "media_title": s["attributes"].get("media_title"),
            "media_artist": s["attributes"].get("media_artist"),
        }
        for s in by_domain("media_player")
        if s["state"] in ("playing", "paused")
    ]

    # Open covers
    covers_open = [
        s["attributes"].get("friendly_name", s["entity_id"])
        for s in by_domain("cover") if s["state"] == "open"
    ]

    # Climate
    climate = [
        {
            "name": s["attributes"].get("friendly_name", s["entity_id"]),
            "hvac_mode": s["state"],
            "current_temp": s["attributes"].get("current_temperature"),
            "target_temp": s["attributes"].get("temperature"),
        }
        for s in by_domain("climate") if s["state"] not in ("unavailable", "unknown", "off")
    ]

    # Active alerts / binary sensors on
    alerts = [
        s["attributes"].get("friendly_name", s["entity_id"])
        for s in by_domain("binary_sensor")
        if s["state"] == "on" and s["attributes"].get("device_class") in (
            "motion", "door", "window", "smoke", "gas", "moisture", "problem", "safety"
        )
    ]

    # Remote instances — auto-detected from remote_homeassistant connection sensors
    import re
    remote_instances = []
    for s in all_states:
        m = re.match(r"sensor\.remote_connection_to_(.+)$", s["entity_id"])
        if not m:
            continue
        remote_instances.append({
            "instance": m.group(1),
            "connected": s["state"] not in ("unavailable", "disconnected", "unknown"),
        })

    return {
        "persons": persons,
        "lights_on": lights_on,
        "lights_on_count": len(lights_on),
        "alarm": alarms,
        "media_active": media_active,
        "covers_open": covers_open,
        "climate_active": climate,
        "active_alerts": alerts,
        "remote_instances": remote_instances,
    }


@mcp.tool()
def get_entity_dependencies(entity_id: str) -> dict:
    """
    Find all automations and scripts that reference a given entity_id.

    Searches through the full config of each automation and script (triggers,
    conditions, actions). Useful before renaming or deleting an entity.

    Returns: {entity_id, automations: [...], scripts: [...], total_searched}
    Note: searches up to 200 automations and 200 scripts in parallel.
    """
    import concurrent.futures
    import json as _json

    with httpx.Client() as client:
        r = client.get(f"{HA_URL}/api/states", headers=HEADERS, timeout=15)
        r.raise_for_status()
        all_states = r.json()

    automations = [s for s in all_states if s["entity_id"].startswith("automation.")]
    scripts = [s for s in all_states if s["entity_id"].startswith("script.")]

    def _check_automation(state):
        slug = state["entity_id"].removeprefix("automation.")
        auto_id = state.get("attributes", {}).get("id") or slug
        try:
            with httpx.Client() as c:
                r = c.get(f"{HA_URL}/api/config/automation/config/{auto_id}", headers=HEADERS, timeout=5)
                if r.status_code != 200:
                    return None
                if entity_id in _json.dumps(r.json()):
                    return {
                        "entity_id": state["entity_id"],
                        "name": state.get("attributes", {}).get("friendly_name", state["entity_id"]),
                        "type": "automation",
                    }
        except Exception:
            pass
        return None

    def _check_script(state):
        slug = state["entity_id"].removeprefix("script.")
        try:
            with httpx.Client() as c:
                r = c.get(f"{HA_URL}/api/config/script/config/{slug}", headers=HEADERS, timeout=5)
                if r.status_code != 200:
                    return None
                if entity_id in _json.dumps(r.json()):
                    return {
                        "entity_id": state["entity_id"],
                        "name": state.get("attributes", {}).get("friendly_name", state["entity_id"]),
                        "type": "script",
                    }
        except Exception:
            pass
        return None

    dep_automations, dep_scripts = [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
        for res in pool.map(_check_automation, automations[:200]):
            if res:
                dep_automations.append(res)
        for res in pool.map(_check_script, scripts[:200]):
            if res:
                dep_scripts.append(res)

    return {
        "entity_id": entity_id,
        "automations": sorted(dep_automations, key=lambda x: x["name"]),
        "scripts": sorted(dep_scripts, key=lambda x: x["name"]),
        "total_automations_searched": len(automations),
        "total_scripts_searched": len(scripts),
    }


@mcp.tool()
def get_entity_exposure() -> list:
    """
    List which entities are exposed to Home Assistant voice assistants
    (Assist, Alexa, Google Assistant, etc.).

    Returns: [{entity_id, assistants: {assist: bool, amazon_alexa: bool, google_assistant: bool}}]
    Only returns entities with at least one exposure setting configured.
    Useful to audit what the voice assistant can control.
    """
    result = _ws({"type": "conversation/expose_entity/list"})
    exposed = (result.get("result") or {}).get("exposed_entities", [])
    out = []
    for e in exposed:
        assistants = e.get("assistants", {})
        if assistants:
            out.append({
                "entity_id": e.get("entity_id"),
                "assistants": assistants,
            })
    return sorted(out, key=lambda x: x["entity_id"])


@mcp.tool()
def search_entities(
    query: str,
    domain: str = "",
    area_id: str = "",
    label: str = "",
    state: str = "",
    limit: int = 50,
) -> list:
    """
    Search for entities across all domains using multiple filters simultaneously.

    query:   substring to search in entity_id or friendly_name (case-insensitive).
             Leave empty to search by other filters only.
    domain:  restrict to a specific domain, e.g. 'light', 'sensor', 'switch'
    area_id: filter by area ID (use list_areas() to find area IDs)
    label:   filter by label ID (use list_labels() to find label IDs)
    state:   filter by exact state value, e.g. 'on', 'off', 'unavailable', '23.5'
    limit:   max results to return (default 50)

    Returns: [{entity_id, name, domain, state, area_id, labels}]

    Examples:
      Find all temperature sensors in the living room:
        query='temperature', domain='sensor', area_id='living_room'
      Find all lights that are on:
        domain='light', state='on'
      Find entities carrying a given label:
        label='outdoor'
    """
    # Fetch states and entity registry in parallel
    ws_result = _ws({"type": "config/entity_registry/list"})
    registry = {e["entity_id"]: e for e in ws_result.get("result", [])}

    with httpx.Client() as client:
        r = client.get(f"{HA_URL}/api/states", headers=HEADERS, timeout=15)
        r.raise_for_status()
        all_states = r.json()

    q = query.lower() if query else ""
    out = []
    for s in all_states:
        eid = s["entity_id"]
        eid_domain = eid.split(".")[0]
        name = s.get("attributes", {}).get("friendly_name", eid)
        reg_entry = registry.get(eid, {})

        # Apply filters
        if domain and eid_domain != domain:
            continue
        if state and s["state"] != state:
            continue
        if area_id and reg_entry.get("area_id") != area_id:
            continue
        if label and label not in reg_entry.get("labels", []):
            continue
        if q and q not in eid.lower() and q not in name.lower():
            continue

        out.append({
            "entity_id": eid,
            "name": name,
            "domain": eid_domain,
            "state": s["state"],
            "area_id": reg_entry.get("area_id"),
            "labels": list(reg_entry.get("labels", [])),
        })
        if len(out) >= limit:
            break

    return out


@mcp.tool()
def get_system_health() -> dict:
    """
    Get Home Assistant system health report via WebSocket.

    Returns the health status of each installed integration that exposes health data
    (e.g. network reachability, authentication, cloud connection status).

    Useful for diagnosing connectivity issues with specific integrations.
    """
    result = _ws({"type": "system_health/info"})
    if result.get("success", True) and result.get("result"):
        data = result["result"]
        # Flatten nested structure: {domain: {info: {key: value|{type,error}}}}
        out = {}
        for domain, section in data.items():
            info = section.get("info", {}) if isinstance(section, dict) else {}
            out[domain] = {
                k: v if not isinstance(v, dict) else f"[{v.get('type', 'error')}] {v.get('error', '')}"
                for k, v in info.items()
            }
        return out

    # Fallback: WS returns null via Supervisor proxy — return basic info from REST config
    with httpx.Client() as client:
        r = client.get(f"{HA_URL}/api/config", headers=HEADERS, timeout=10)
        r.raise_for_status()
        cfg = r.json()
    return {
        "homeassistant": {
            "version": cfg.get("version"),
            "location_name": cfg.get("location_name"),
            "time_zone": cfg.get("time_zone"),
            "components_count": len(cfg.get("components", [])),
        },
        "_note": "Full system_health/info not available via Supervisor proxy — showing basic config info",
    }


@mcp.tool()
def call_service(domain: str, service: str, entity_id: str = "", service_data: dict = None) -> list:
    """
    Call any Home Assistant service.

    Examples:
    - Turn on a light: domain='light', service='turn_on', entity_id='light.living_room'
    - Set brightness:  domain='light', service='turn_on', entity_id='light.living_room',
                       service_data={'brightness_pct': 80}
    - Reload config:   domain='homeassistant', service='reload_config_entry'
    """
    data = dict(service_data) if service_data else {}
    if entity_id:
        data["entity_id"] = entity_id
    with httpx.Client() as client:
        r = client.post(
            f"{HA_URL}/api/services/{domain}/{service}",
            headers=HEADERS,
            json=data,
            timeout=15,
        )
        r.raise_for_status()
        return r.json()
