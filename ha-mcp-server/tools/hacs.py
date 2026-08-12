from tools._base import mcp, _ws


def _hacs_check(result: dict):
    """Return an error dict if the WS call failed (e.g. HACS not installed)."""
    if not result.get("success", True):
        err = result.get("error", {})
        code = err.get("code", "unknown")
        if code in ("unknown_command", "not_found"):
            return {
                "error": "hacs_not_available",
                "detail": "HACS is not installed or not running on this Home Assistant instance.",
            }
        return {"error": code, "detail": err.get("message", str(err))}
    return None


@mcp.tool()
def hacs_info() -> dict:
    """
    Get general HACS status: version, stage, categories, pending tasks.
    Useful to confirm HACS is installed and running before other HACS operations.
    """
    result = _ws({"type": "hacs/info"})
    err = _hacs_check(result)
    if err:
        return err
    return result.get("result", {})


@mcp.tool()
def list_hacs_repos(
    category: str = "",
    installed_only: bool = False,
    updates_only: bool = False,
) -> list:
    """
    List repositories known to HACS (installed and available in the catalog).

    category:      filter by category — 'integration', 'plugin', 'theme',
                   'appdaemon', 'python_script', 'template'. Leave empty for all.
    installed_only: if True, return only installed repositories.
    updates_only:  if True, return only repositories with a pending update.

    Returns: [{id, full_name, name, category, installed, installed_version,
               available_version, pending_upgrade, custom, stars, description}]
    """
    msg: dict = {"type": "hacs/repositories/list"}
    if category:
        msg["categories"] = [category]
    result = _ws(msg)
    err = _hacs_check(result)
    if err:
        return [err]
    repos = result.get("result", [])
    if installed_only:
        repos = [r for r in repos if r.get("installed")]
    if updates_only:
        repos = [r for r in repos if r.get("pending_upgrade")]
    return [
        {
            "id": r.get("id"),
            "full_name": r.get("full_name"),
            "name": r.get("name") or r.get("full_name", ""),
            "category": r.get("category"),
            "installed": r.get("installed", False),
            "installed_version": r.get("installed_version"),
            "available_version": r.get("available_version"),
            "pending_upgrade": r.get("pending_upgrade", False),
            "custom": r.get("custom", False),
            "stars": r.get("stars", 0),
            "description": r.get("description", ""),
        }
        for r in repos
    ]


@mcp.tool()
def search_hacs(query: str, category: str = "") -> list:
    """
    Search HACS catalog for repositories matching a query string.

    query:    substring to search in name, full_name, or description (case-insensitive)
    category: optional filter — 'integration', 'plugin', 'theme', 'appdaemon',
              'python_script', 'template'

    Returns the top 20 matches sorted by stars.
    """
    msg: dict = {"type": "hacs/repositories/list"}
    if category:
        msg["categories"] = [category]
    result = _ws(msg)
    err = _hacs_check(result)
    if err:
        return [err]
    repos = result.get("result", [])
    q = query.lower()
    matches = [
        r for r in repos
        if q in (r.get("name") or "").lower()
        or q in (r.get("full_name") or "").lower()
        or q in (r.get("description") or "").lower()
    ]
    matches.sort(key=lambda x: x.get("stars", 0), reverse=True)
    return [
        {
            "id": r.get("id"),
            "full_name": r.get("full_name"),
            "name": r.get("name") or r.get("full_name", ""),
            "category": r.get("category"),
            "installed": r.get("installed", False),
            "installed_version": r.get("installed_version"),
            "available_version": r.get("available_version"),
            "stars": r.get("stars", 0),
            "description": r.get("description", ""),
        }
        for r in matches[:20]
    ]


@mcp.tool()
def get_hacs_repo(repository_id: str) -> dict:
    """
    Get detailed info about a specific HACS repository.

    repository_id: numeric ID string (use list_hacs_repos() or search_hacs() to find it)

    Returns full details including releases, authors, topics, and install status.
    """
    result = _ws({"type": "hacs/repository/info", "repository_id": repository_id})
    err = _hacs_check(result)
    if err:
        return err
    return result.get("result", {})


@mcp.tool()
def install_hacs_repo(repository_id: str, version: str = "") -> dict:
    """
    Install or update a HACS repository.

    repository_id: numeric ID string (use search_hacs() or list_hacs_repos() to find it)
    version:       specific version/tag to install (leave empty for latest)

    ⚠️ Integrations require a Home Assistant restart to take effect.
    Lovelace plugins and themes are active immediately.
    """
    msg: dict = {"type": "hacs/repository/download", "repository": repository_id}
    if version:
        msg["version"] = version
    result = _ws(msg)
    err = _hacs_check(result)
    if err:
        return err
    return {
        "installed": True,
        "repository_id": repository_id,
        "version": version or "latest",
    }


@mcp.tool()
def remove_hacs_repo(repository_id: str) -> dict:
    """
    Uninstall a HACS repository (removes files from disk).

    repository_id: numeric ID string (use list_hacs_repos(installed_only=True) to find it)

    Note: this removes the custom component / plugin files. A HA restart may be needed
    to fully remove the integration. To only remove the repository from the HACS list
    without deleting files, this is not the right tool.
    """
    result = _ws({"type": "hacs/repository/remove", "repository": repository_id})
    err = _hacs_check(result)
    if err:
        return err
    return {"removed": True, "repository_id": repository_id}


@mcp.tool()
def add_hacs_custom_repo(repository: str, category: str) -> dict:
    """
    Add a custom repository to HACS (does not install it — just registers it).

    repository: GitHub URL or 'owner/repo' string
                e.g. 'https://github.com/custom-cards/button-card' or 'custom-cards/button-card'
    category:   repository type — 'integration', 'plugin', 'theme',
                'appdaemon', 'python_script', 'template'

    After adding, use search_hacs() to find the repo ID and install_hacs_repo() to install it.
    """
    result = _ws({"type": "hacs/repositories/add", "repository": repository, "category": category})
    err = _hacs_check(result)
    if err:
        return err
    return {"added": True, "repository": repository, "category": category}
