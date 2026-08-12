import httpx

from tools._base import mcp, HA_URL, HEADERS, _ws, _ws_multi


@mcp.tool()
def restart_homeassistant() -> dict:
    """
    Restart Home Assistant. Use with caution — all automations and integrations
    will be unavailable for ~30–60 seconds during restart.
    """
    with httpx.Client() as client:
        r = client.post(
            f"{HA_URL}/api/services/homeassistant/restart",
            headers=HEADERS,
            json={},
            timeout=15,
        )
        r.raise_for_status()
    return {"restarting": True}


@mcp.tool()
def list_config_entries(domain: str = "") -> list:
    """
    List installed integrations (config entries).
    domain: optional filter (e.g. 'telegram_bot', 'shelly', 'reolink')
    """
    result = _ws({"type": "config_entries/list"})
    entries = result.get("result", [])
    out = []
    for e in entries:
        if domain and e.get("domain") != domain:
            continue
        out.append({
            "entry_id": e.get("entry_id"),
            "domain": e.get("domain"),
            "title": e.get("title"),
            "state": e.get("state"),
            "disabled_by": e.get("disabled_by"),
        })
    return sorted(out, key=lambda x: (x["domain"], x["title"]))


@mcp.tool()
def list_repairs() -> list:
    """List all active repair issues in Home Assistant."""
    result = _ws({"type": "repairs/list_issues"})
    issues = (result.get("result") or {}).get("issues", [])
    return [
        {
            "issue_id": i.get("issue_id"),
            "domain": i.get("domain"),
            "severity": i.get("severity"),
            "title": i.get("translation_key"),
            "ignored": i.get("ignored", False),
            "created": i.get("created"),
        }
        for i in issues
        if not i.get("ignored", False)
    ]


@mcp.tool()
def list_backups() -> list:
    """List all available backups in Home Assistant."""
    result = _ws({"type": "backup/info"})
    data = result.get("result") or {}
    backups = data.get("backups", [])
    return [
        {
            "backup_id": b.get("backup_id") or b.get("slug"),
            "name": b.get("name"),
            "date": b.get("date"),
            "size_mb": round(b.get("size", 0) / 1048576, 1) if b.get("size") else None,
            "type": b.get("type", "full"),
            "protected": b.get("protected", False),
            "homeassistant_version": b.get("homeassistant_version") or b.get("homeassistant"),
        }
        for b in sorted(backups, key=lambda x: x.get("date", ""), reverse=True)
    ]


@mcp.tool()
def create_backup(name: str = "") -> dict:
    """
    Create a new full backup of Home Assistant.
    name: optional backup name (defaults to HA's auto-generated name)
    Note: backup creation is asynchronous — it may take several minutes to complete.
    """
    msg: dict = {"type": "backup/generate"}
    if name:
        msg["name"] = name
    result = _ws(msg)
    return result.get("result") or result


@mcp.tool()
def reload_integration(entry_id: str) -> dict:
    """
    Reload a config entry (integration) without restarting Home Assistant.
    entry_id: use list_config_entries() to find the entry_id.
    """
    result = _ws({"type": "config_entries/reload", "entry_id": entry_id})
    return {"entry_id": entry_id, "reloaded": result.get("result", False), "success": result.get("success", False)}


@mcp.tool()
def apply_update(entity_id: str, backup: bool = True) -> dict:
    """
    Install a pending update (HA core, add-on, HACS integration, firmware, etc.).

    entity_id: the update.* entity to install (use list_updates() to find them)
    backup: create a backup before updating (default: True, recommended)

    ⚠️ Some updates require a restart. Confirm with the user before proceeding.
    """
    with httpx.Client() as client:
        r = client.post(
            f"{HA_URL}/api/services/update/install",
            headers=HEADERS,
            json={"entity_id": entity_id, "backup": backup},
            timeout=30,
        )
        r.raise_for_status()
    return {"entity_id": entity_id, "update_triggered": True, "backup": backup}


@mcp.tool()
def list_updates() -> list:
    """List all available updates (HA core, HACS integrations, add-ons, etc.)."""
    with httpx.Client() as client:
        r = client.get(f"{HA_URL}/api/states", headers=HEADERS, timeout=15)
        r.raise_for_status()
        updates = []
        for s in r.json():
            if not s["entity_id"].startswith("update."):
                continue
            if s["state"] != "on":
                continue
            attrs = s.get("attributes", {})
            updates.append({
                "entity_id": s["entity_id"],
                "name": attrs.get("friendly_name", s["entity_id"]),
                "installed_version": attrs.get("installed_version"),
                "latest_version": attrs.get("latest_version"),
                "release_url": attrs.get("release_url", ""),
                "skipped_version": attrs.get("skipped_version"),
            })
        return sorted(updates, key=lambda x: x["name"])


@mcp.tool()
def list_config_flows() -> list:
    """
    List pending integration setup flows (config entries in progress).

    These are integrations that have been discovered or partially configured
    and are waiting for user action (e.g. approval, credentials, device selection).

    Returns: [{flow_id, handler, step_id, context, description_placeholders}]
    Use dismiss_config_flow() to cancel a pending flow.
    """
    def _parse(flows):
        return [
            {
                "flow_id": f.get("flow_id"),
                "handler": f.get("handler"),
                "step_id": f.get("step_id"),
                "context": f.get("context", {}),
                "description_placeholders": f.get("description_placeholders", {}),
            }
            for f in (flows if isinstance(flows, list) else [])
        ]

    # Try WS first (works across all HA setups including Supervisor)
    result = _ws({"type": "config_entries/flow/progress"})
    if result.get("success", True) and "result" in result:
        return _parse(result.get("result", []))

    # Fallback: REST (not always available via Supervisor proxy)
    try:
        with httpx.Client() as client:
            r = client.get(
                f"{HA_URL}/api/config/config_entries/flow",
                headers=HEADERS,
                timeout=10,
            )
            if r.status_code == 200:
                return _parse(r.json())
    except Exception:
        pass

    return []


@mcp.tool()
def dismiss_config_flow(flow_id: str) -> dict:
    """
    Cancel and dismiss a pending integration setup flow.

    flow_id: use list_config_flows() to find the flow_id.
    This removes the flow without completing the integration setup.
    Useful for dismissing unwanted auto-discovered integrations.
    """
    with httpx.Client() as client:
        r = client.delete(
            f"{HA_URL}/api/config/config_entries/flow/{flow_id}",
            headers=HEADERS,
            timeout=10,
        )
        r.raise_for_status()
    return {"dismissed": flow_id, "success": True}
