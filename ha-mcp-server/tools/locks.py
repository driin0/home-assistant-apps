import httpx

from tools._base import mcp, HA_URL, HEADERS


@mcp.tool()
def list_locks() -> list:
    """List all lock entities with their state."""
    with httpx.Client() as client:
        r = client.get(f"{HA_URL}/api/states", headers=HEADERS, timeout=15)
        r.raise_for_status()
    locks = []
    for s in r.json():
        if not s["entity_id"].startswith("lock."):
            continue
        attrs = s.get("attributes", {})
        locks.append({
            "entity_id": s["entity_id"],
            "name": attrs.get("friendly_name", s["entity_id"]),
            "state": s["state"],
            "changed_by": attrs.get("changed_by"),
        })
    return sorted(locks, key=lambda x: x["name"])


@mcp.tool()
def lock_control(entity_id: str, command: str, code: str = "") -> dict:
    """
    Control a lock entity.

    ⚠️ SAFETY: This physically actuates a lock. ALWAYS ask the user for explicit
    confirmation before calling this tool — show the entity name and command,
    then wait for the user to confirm before proceeding.

    command: lock | unlock | open
    code: optional PIN/code if required by the lock
    """
    if command not in ("lock", "unlock", "open"):
        raise ValueError("command must be: lock, unlock, or open")
    data: dict = {"entity_id": entity_id}
    if code:
        data["code"] = code
    with httpx.Client() as client:
        r = client.post(f"{HA_URL}/api/services/lock/{command}", headers=HEADERS, json=data, timeout=10)
        r.raise_for_status()
    return {"entity_id": entity_id, "command": command, "ok": True}
