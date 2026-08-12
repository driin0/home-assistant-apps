from tools._base import mcp, _ws


def _dashboard_id(url_path: str) -> str:
    """Resolve a dashboard url_path to the id the WebSocket API expects.

    The lovelace/dashboards/update and /delete commands are keyed by
    dashboard_id and reject url_path outright, while url_path is what a user
    sees and what list_dashboards() reports — so it is translated here.
    """
    result = _ws({"type": "lovelace/dashboards/list"})
    for d in result.get("result") or []:
        if d.get("url_path") == url_path:
            return d.get("id", "")
    return ""


@mcp.tool()
def list_dashboards() -> list:
    """
    List all Lovelace dashboards configured in Home Assistant.

    Returns: [{url_path, title, mode, icon, show_in_sidebar, require_admin}]
    mode is 'storage' (UI-managed) or 'yaml' (file-based).
    """
    result = _ws({"type": "lovelace/dashboards/list"})
    dashboards = result.get("result", [])
    out = []
    for d in dashboards:
        out.append({
            "url_path": d.get("url_path"),
            "title": d.get("title") or d.get("url_path") or "default",
            "mode": d.get("mode", "storage"),
            "icon": d.get("icon", ""),
            "show_in_sidebar": d.get("show_in_sidebar", True),
            "require_admin": d.get("require_admin", False),
        })
    return sorted(out, key=lambda x: (x.get("title") or "").lower())


@mcp.tool()
def get_dashboard(url_path: str = "") -> dict:
    """
    Get the full configuration (views and cards) of a Lovelace dashboard.

    url_path: dashboard URL path (e.g. 'lovelace', 'mobile', 'energia').
              Leave empty for the default dashboard.

    Returns the raw dashboard config. For large dashboards this can be verbose —
    use a specific url_path to limit output.
    """
    msg: dict = {"type": "lovelace/config"}
    if url_path:
        msg["url_path"] = url_path
    msg["force"] = False
    result = _ws(msg)
    if not result.get("success", True):
        err = result.get("error", {})
        return {"error": err.get("code", "unknown"), "detail": err.get("message", "")}
    return result.get("result", {})


@mcp.tool()
def create_dashboard(
    url_path: str,
    title: str,
    icon: str = "",
    show_in_sidebar: bool = True,
    require_admin: bool = False,
) -> dict:
    """
    Create a new Lovelace dashboard (storage mode).

    url_path:        unique URL slug for the dashboard (e.g. 'mobile', 'energia', 'admin')
    title:           display title shown in the sidebar
    icon:            MDI icon, e.g. 'mdi:solar-power' (optional)
    show_in_sidebar: show in left navigation (default: True)
    require_admin:   restrict access to admins only (default: False)

    After creating, use update_dashboard_config() to populate views and cards.
    """
    msg: dict = {
        "type": "lovelace/dashboards/create",
        "url_path": url_path,
        "title": title,
        "mode": "storage",
        "show_in_sidebar": show_in_sidebar,
        "require_admin": require_admin,
    }
    if icon:
        msg["icon"] = icon
    result = _ws(msg)
    if not result.get("success", True):
        err = result.get("error", {})
        return {"error": err.get("code", "unknown"), "detail": err.get("message", "")}
    return result.get("result", result)


@mcp.tool()
def update_dashboard(
    url_path: str,
    title: str = "",
    icon: str = "",
    show_in_sidebar: bool = None,
    require_admin: bool = None,
) -> dict:
    """
    Update a Lovelace dashboard's metadata (title, icon, sidebar visibility).

    url_path: dashboard URL path to update (use list_dashboards() to find url_paths).
    Only fields with non-None/non-empty values are updated.

    To update the actual views and cards content, use update_dashboard_config() instead.
    """
    dashboard_id = _dashboard_id(url_path)
    if not dashboard_id:
        return {"error": "not_found", "url_path": url_path,
                "detail": "No dashboard with that url_path. Use list_dashboards()."}
    msg: dict = {"type": "lovelace/dashboards/update", "dashboard_id": dashboard_id}
    if title:
        msg["title"] = title
    if icon:
        msg["icon"] = icon
    if show_in_sidebar is not None:
        msg["show_in_sidebar"] = show_in_sidebar
    if require_admin is not None:
        msg["require_admin"] = require_admin
    result = _ws(msg)
    if not result.get("success", True):
        err = result.get("error", {})
        return {"error": err.get("code", "unknown"), "detail": err.get("message", "")}
    return result.get("result", result)


@mcp.tool()
def update_dashboard_config(url_path: str, config: dict) -> dict:
    """
    Save the full configuration (views and cards) of a Lovelace dashboard.

    url_path: dashboard URL path (use empty string '' for the default dashboard).
    config:   complete Lovelace config dict with a 'views' list. Example:
    {
      "views": [
        {
          "title": "Home",
          "path": "home",
          "icon": "mdi:home",
          "cards": [
            {"type": "entities", "title": "Lights", "entities": ["light.living_room", "light.kitchen"]},
            {"type": "weather-forecast", "entity": "weather.home"}
          ]
        }
      ]
    }

    ⚠️ This REPLACES the entire dashboard config. Call get_dashboard() first
    to read the current config if you want to make incremental changes.
    """
    msg: dict = {"type": "lovelace/config/save", "config": config}
    if url_path:
        msg["url_path"] = url_path
    result = _ws(msg)
    if not result.get("success", True):
        err = result.get("error", {})
        return {"error": err.get("code", "unknown"), "detail": err.get("message", "")}
    return {"saved": True, "url_path": url_path or "default"}


@mcp.tool()
def delete_dashboard(url_path: str) -> dict:
    """
    Delete a Lovelace dashboard.

    url_path: dashboard URL path (use list_dashboards() to find url_paths).
    Note: the default dashboard cannot be deleted.
    """
    dashboard_id = _dashboard_id(url_path)
    if not dashboard_id:
        return {"error": "not_found", "url_path": url_path,
                "detail": "No dashboard with that url_path. Use list_dashboards()."}
    result = _ws({"type": "lovelace/dashboards/delete", "dashboard_id": dashboard_id})
    if not result.get("success", True):
        err = result.get("error", {})
        return {"error": err.get("code", "unknown"), "detail": err.get("message", "")}
    return {"deleted": url_path, "success": True}


# ─── Lovelace frontend resources ─────────────────────────────────────────────

@mcp.tool()
def list_lovelace_resources() -> list:
    """
    List all Lovelace frontend resources (JavaScript modules and CSS stylesheets).

    These are the custom card JS files and theme CSS files loaded by the HA frontend.
    Useful to audit what's installed or to add new custom cards manually.

    Returns: [{id, url, type}]  — type is 'module' (JS) or 'css'
    """
    result = _ws({"type": "lovelace/resources/list"})
    if not result.get("success", True):
        err = result.get("error", {})
        return [{"error": err.get("code", "unknown"), "detail": err.get("message", "")}]
    return [
        {
            "id": r.get("id"),
            "url": r.get("url"),
            "type": r.get("res_type", r.get("type", "")),
        }
        for r in (result.get("result") or [])
    ]


@mcp.tool()
def add_lovelace_resource(url: str, resource_type: str = "module") -> dict:
    """
    Add a Lovelace frontend resource (custom card JS or CSS stylesheet).

    url:           URL to the resource, e.g. '/hacsfiles/button-card/button-card.js'
                   or 'https://cdn.example.com/my-card.js'
    resource_type: 'module' (default, for ES module JS files) or 'css'

    After adding a JS module, reload the browser to load the new card.
    Note: HACS-installed cards are added automatically — use this for manual installs.
    """
    result = _ws({"type": "lovelace/resources/create", "url": url, "res_type": resource_type})
    if not result.get("success", True):
        err = result.get("error", {})
        return {"error": err.get("code", "unknown"), "detail": err.get("message", "")}
    return result.get("result", {"added": True, "url": url, "type": resource_type})


@mcp.tool()
def remove_lovelace_resource(resource_id: int) -> dict:
    """
    Remove a Lovelace frontend resource by its ID.

    resource_id: integer ID (use list_lovelace_resources() to find IDs)
    """
    result = _ws({"type": "lovelace/resources/delete", "id": resource_id})
    if not result.get("success", True):
        err = result.get("error", {})
        return {"error": err.get("code", "unknown"), "detail": err.get("message", "")}
    return {"deleted": resource_id, "success": True}
