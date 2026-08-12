import os

import httpx

from tools._base import mcp, HA_URL, HA_TOKEN

# Supervisor API is available only in HA OS / Supervised add-on context.
# In the add-on, HA_URL = "http://supervisor/core" and the token is the SUPERVISOR_TOKEN.
# We detect this by checking if HA_URL points to the supervisor proxy.
_SUPERVISOR_TOKEN = os.getenv("SUPERVISOR_TOKEN", "") or HA_TOKEN
_SUPERVISOR_BASE = "http://supervisor" if "supervisor" in HA_URL else None
_SUPERVISOR_HEADERS = {
    "Authorization": f"Bearer {_SUPERVISOR_TOKEN}",
    "Content-Type": "application/json",
}


def _check_supervisor():
    """Return an error dict if Supervisor API is not available, else None."""
    if not _SUPERVISOR_BASE:
        return {
            "error": "supervisor_not_available",
            "detail": (
                "Add-on management requires Home Assistant OS or Supervised installation. "
                "This feature is not available in standalone mode."
            ),
        }
    return None


@mcp.tool()
def list_addons(search: str = "") -> list:
    """
    List all installed add-ons with their current state and version.

    search: optional substring filter on name or slug (case-insensitive)

    Returns: [{slug, name, version, version_latest, state, update_available, repository}]
    Requires: Home Assistant OS or Supervised installation.
    """
    err = _check_supervisor()
    if err:
        return [err]
    with httpx.Client() as client:
        r = client.get(f"{_SUPERVISOR_BASE}/addons", headers=_SUPERVISOR_HEADERS, timeout=15)
        r.raise_for_status()
    addons = r.json().get("data", {}).get("addons", [])
    out = []
    for a in addons:
        if search and search.lower() not in a.get("name", "").lower() and search.lower() not in a.get("slug", "").lower():
            continue
        out.append({
            "slug": a.get("slug"),
            "name": a.get("name"),
            "version": a.get("version"),
            "version_latest": a.get("version_latest"),
            "state": a.get("state"),           # started | stopped | unknown
            "update_available": a.get("update_available", False),
            "repository": a.get("repository"),
            "description": a.get("description", ""),
        })
    return sorted(out, key=lambda x: (x.get("name") or "").lower())


@mcp.tool()
def get_addon(slug: str) -> dict:
    """
    Get detailed information about a specific add-on.

    slug: add-on slug, e.g. 'core_mosquitto', 'a0d7b954_zigbee2mqtt'
    Use list_addons() to discover slugs.
    """
    err = _check_supervisor()
    if err:
        return err
    with httpx.Client() as client:
        r = client.get(f"{_SUPERVISOR_BASE}/addons/{slug}/info", headers=_SUPERVISOR_HEADERS, timeout=15)
        r.raise_for_status()
    d = r.json().get("data", {})
    return {
        "slug": d.get("slug"),
        "name": d.get("name"),
        "description": d.get("description"),
        "version": d.get("version"),
        "version_latest": d.get("version_latest"),
        "update_available": d.get("update_available", False),
        "state": d.get("state"),
        "boot": d.get("boot"),         # auto | manual
        "options": d.get("options", {}),
        "network": d.get("network"),
        "homeassistant_api": d.get("homeassistant_api", False),
        "ingress": d.get("ingress", False),
        "ingress_url": d.get("ingress_url"),
        "watchdog": d.get("watchdog", False),
        "auto_update": d.get("auto_update", False),
    }


@mcp.tool()
def start_addon(slug: str) -> dict:
    """
    Start an add-on.

    slug: add-on slug, e.g. 'core_mosquitto'. Use list_addons() to find slugs.
    """
    err = _check_supervisor()
    if err:
        return err
    with httpx.Client() as client:
        r = client.post(f"{_SUPERVISOR_BASE}/addons/{slug}/start", headers=_SUPERVISOR_HEADERS, timeout=30)
        r.raise_for_status()
    return {"slug": slug, "action": "start", "result": r.json().get("result", "ok")}


@mcp.tool()
def stop_addon(slug: str) -> dict:
    """
    Stop a running add-on.

    slug: add-on slug, e.g. 'core_mosquitto'. Use list_addons() to find slugs.
    """
    err = _check_supervisor()
    if err:
        return err
    with httpx.Client() as client:
        r = client.post(f"{_SUPERVISOR_BASE}/addons/{slug}/stop", headers=_SUPERVISOR_HEADERS, timeout=30)
        r.raise_for_status()
    return {"slug": slug, "action": "stop", "result": r.json().get("result", "ok")}


@mcp.tool()
def restart_addon(slug: str) -> dict:
    """
    Restart an add-on (stop then start).

    slug: add-on slug, e.g. 'core_mosquitto'. Use list_addons() to find slugs.
    """
    err = _check_supervisor()
    if err:
        return err
    with httpx.Client() as client:
        r = client.post(f"{_SUPERVISOR_BASE}/addons/{slug}/restart", headers=_SUPERVISOR_HEADERS, timeout=30)
        r.raise_for_status()
    return {"slug": slug, "action": "restart", "result": r.json().get("result", "ok")}


@mcp.tool()
def get_addon_logs(slug: str, lines: int = 100) -> str:
    """
    Get the latest log output from an add-on.

    slug:  add-on slug, e.g. 'core_mosquitto'. Use list_addons() to find slugs.
    lines: number of recent log lines to return (default 100)
    """
    err = _check_supervisor()
    if err:
        return str(err)
    with httpx.Client() as client:
        r = client.get(f"{_SUPERVISOR_BASE}/addons/{slug}/logs", headers=_SUPERVISOR_HEADERS, timeout=15)
        r.raise_for_status()
    return "\n".join(r.text.splitlines()[-lines:])


@mcp.tool()
def get_supervisor_info() -> dict:
    """
    Get Home Assistant Supervisor and OS info: version, update availability,
    channel (stable/beta/dev), and system architecture.

    Requires: Home Assistant OS or Supervised installation.
    """
    err = _check_supervisor()
    if err:
        return err
    with httpx.Client() as client:
        sup_r = client.get(f"{_SUPERVISOR_BASE}/supervisor/info", headers=_SUPERVISOR_HEADERS, timeout=10)
        os_r = client.get(f"{_SUPERVISOR_BASE}/os/info", headers=_SUPERVISOR_HEADERS, timeout=10)
    sup = sup_r.json().get("data", {}) if sup_r.status_code == 200 else {}
    os_info = os_r.json().get("data", {}) if os_r.status_code == 200 else {}
    return {
        "supervisor_version": sup.get("version"),
        "supervisor_latest": sup.get("version_latest"),
        "supervisor_update_available": sup.get("update_available", False),
        "channel": sup.get("channel"),
        "arch": sup.get("arch"),
        "ha_os_version": os_info.get("version"),
        "ha_os_latest": os_info.get("version_latest"),
        "ha_os_update_available": os_info.get("update_available", False),
        "board": os_info.get("board"),
    }


@mcp.tool()
def call_addon_api(
    slug: str,
    path: str,
    method: str = "GET",
    data: dict = None,
) -> dict:
    """
    Call an add-on's internal HTTP API via the Supervisor proxy.

    slug:   add-on slug, e.g. 'a0d7b954_zigbee2mqtt'. Use list_addons() to find slugs.
    path:   API path within the add-on, e.g. '/api/devices', '/health', '/api/permit'
    method: HTTP method — 'GET' (default), 'POST', 'PUT', 'DELETE'
    data:   optional request body dict for POST/PUT requests

    Examples:
      Zigbee2MQTT devices:   slug='a0d7b954_zigbee2mqtt', path='/api/devices'
      ESPHome health:        slug='5c53de3b_esphome', path='/health'
      Node-RED flows:        slug='a0d7b954_nodered', path='/flows'

    Requires: Home Assistant OS or Supervised installation.
    """
    err = _check_supervisor()
    if err:
        return err
    path = path.lstrip("/")
    url = f"{_SUPERVISOR_BASE}/addons/{slug}/api/{path}"
    with httpx.Client() as client:
        if method.upper() == "GET":
            r = client.get(url, headers=_SUPERVISOR_HEADERS, timeout=15)
        elif method.upper() == "POST":
            r = client.post(url, headers=_SUPERVISOR_HEADERS, json=data or {}, timeout=15)
        elif method.upper() == "PUT":
            r = client.put(url, headers=_SUPERVISOR_HEADERS, json=data or {}, timeout=15)
        elif method.upper() == "DELETE":
            r = client.delete(url, headers=_SUPERVISOR_HEADERS, timeout=15)
        else:
            return {"error": f"unsupported_method: {method}"}
        r.raise_for_status()
    try:
        return r.json()
    except Exception:
        return {"text": r.text, "status_code": r.status_code}
