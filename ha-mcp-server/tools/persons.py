import httpx

from tools._base import mcp, HA_URL, HEADERS, _ws


@mcp.tool()
def list_persons() -> list:
    """
    List all person entities with their state (home/away/zone) and GPS coordinates.
    """
    with httpx.Client() as client:
        r = client.get(f"{HA_URL}/api/states", headers=HEADERS, timeout=15)
        r.raise_for_status()
    persons = []
    for s in r.json():
        if not s["entity_id"].startswith("person."):
            continue
        attrs = s.get("attributes", {})
        persons.append({
            "entity_id": s["entity_id"],
            "name": attrs.get("friendly_name", s["entity_id"]),
            "state": s["state"],
            "latitude": attrs.get("latitude"),
            "longitude": attrs.get("longitude"),
            "gps_accuracy": attrs.get("gps_accuracy"),
            "source": attrs.get("source"),
            "last_changed": s.get("last_changed"),
        })
    return sorted(persons, key=lambda x: x["name"])


@mcp.tool()
def create_person(
    name: str,
    user_id: str = "",
    device_trackers: list = None,
) -> dict:
    """
    Create a new person.

    name:            display name, e.g. 'Jane Doe'
    user_id:         optional HA user ID to link this person to a user account
                     (use list_users via WS or leave empty for persons without accounts)
    device_trackers: list of device_tracker entity_ids to track this person's location,
                     e.g. ['device_tracker.jane_phone', 'device_tracker.jane_tablet']
    """
    msg: dict = {"type": "person/create", "name": name}
    if user_id:
        msg["user_id"] = user_id
    if device_trackers:
        msg["device_trackers"] = device_trackers
    result = _ws(msg)
    if not result.get("success", True):
        err = result.get("error", {})
        return {"error": err.get("code", "unknown"), "detail": err.get("message", "")}
    return result.get("result", result)


@mcp.tool()
def update_person(
    person_id: str,
    name: str = "",
    user_id: str = "",
    device_trackers: list = None,
) -> dict:
    """
    Update an existing person's name, linked user, or tracked devices.

    person_id:       person ID (the part after 'person.', e.g. 'jane_doe')
                     Use list_persons() to find entity_ids, then strip 'person.' prefix.
    name:            new display name (leave empty to keep current)
    user_id:         HA user ID to link (pass empty string to unlink)
    device_trackers: new list of device_tracker entity_ids (replaces current list)
    """
    msg: dict = {"type": "person/update", "person_id": person_id}
    if name:
        msg["name"] = name
    if user_id is not None:
        msg["user_id"] = user_id or None
    if device_trackers is not None:
        msg["device_trackers"] = device_trackers
    result = _ws(msg)
    if not result.get("success", True):
        err = result.get("error", {})
        return {"error": err.get("code", "unknown"), "detail": err.get("message", "")}
    return result.get("result", result)


@mcp.tool()
def delete_person(person_id: str) -> dict:
    """
    Delete a person.

    person_id: person ID (the part after 'person.', e.g. 'jane_doe').
               Use list_persons() to find entity_ids, then strip 'person.' prefix.

    Note: only persons created via the UI (not imported from HA user accounts) can be deleted.
    """
    result = _ws({"type": "person/delete", "person_id": person_id})
    if not result.get("success", True):
        err = result.get("error", {})
        return {"error": err.get("code", "unknown"), "detail": err.get("message", "")}
    return {"deleted": person_id, "success": True}
