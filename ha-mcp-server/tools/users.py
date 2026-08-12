import httpx

from tools._base import mcp, HA_URL, HEADERS, _ws


@mcp.tool()
def list_users() -> list:
    """
    List all Home Assistant user accounts.

    Returns: [{id, name, is_admin, is_active, local_only, system_generated}]
    Requires admin privileges.
    """
    # WS config/auth/list — the correct command used by the HA frontend
    result = _ws({"type": "config/auth/list"})
    if not result.get("success", True):
        err = result.get("error", {})
        return [{"error": err.get("code", "unknown"), "detail": err.get("message", "")}]
    users = result.get("result", [])
    return [
        {
            "id": u.get("id"),
            "name": u.get("name"),
            "is_admin": u.get("is_admin", False),
            "is_active": u.get("is_active", True),
            "local_only": u.get("local_only", False),
            "system_generated": u.get("system_generated", False),
        }
        for u in sorted(users, key=lambda x: (x.get("system_generated", False), (x.get("name") or "").lower()))
        if not u.get("system_generated")  # hide internal system accounts
    ]


@mcp.tool()
def create_user(
    name: str,
    is_admin: bool = False,
    local_only: bool = False,
) -> dict:
    """
    Create a new Home Assistant user account.

    name:       display name for the user
    is_admin:   grant admin privileges (default: False)
    local_only: restrict login to local network only (default: False)

    Returns the new user with their ID. Note: this creates the user record
    but does not set a password — the user must complete setup via the HA onboarding flow
    or you can use update_user() to assign them to a person.
    """
    result = _ws({
        "type": "config/auth/create",
        "name": name,
        "group_ids": ["system-admin"] if is_admin else ["system-users"],
        "local_only": local_only,
    })
    if not result.get("success", True):
        err = result.get("error", {})
        return {"error": err.get("code", "unknown"), "detail": err.get("message", "")}
    return result.get("result", {}).get("user", result.get("result", {}))


@mcp.tool()
def update_user(
    user_id: str,
    name: str = "",
    is_admin: bool = None,
    is_active: bool = None,
    local_only: bool = None,
) -> dict:
    """
    Update an existing user account.

    user_id:    user ID (use list_users() to find it)
    name:       new display name
    is_admin:   grant or revoke admin privileges
    is_active:  enable or disable the account
    local_only: restrict to local network only

    Only non-None fields are updated.
    """
    msg: dict = {"type": "config/auth/update", "user_id": user_id}
    if name:
        msg["name"] = name
    if is_admin is not None:
        msg["group_ids"] = ["system-admin"] if is_admin else ["system-users"]
    if is_active is not None:
        msg["is_active"] = is_active
    if local_only is not None:
        msg["local_only"] = local_only
    result = _ws(msg)
    if not result.get("success", True):
        err = result.get("error", {})
        return {"error": err.get("code", "unknown"), "detail": err.get("message", "")}
    return result.get("result", {}).get("user", result.get("result", {}))


@mcp.tool()
def delete_user(user_id: str) -> dict:
    """
    Delete a user account.

    user_id: user ID (use list_users() to find it).
    ⚠️ This is irreversible. The user will lose access immediately.
    Cannot delete the owner account or your own account.
    """
    result = _ws({"type": "config/auth/delete", "user_id": user_id})
    if not result.get("success", True):
        err = result.get("error", {})
        return {"error": err.get("code", "unknown"), "detail": err.get("message", "")}
    return {"deleted": user_id, "success": True}
