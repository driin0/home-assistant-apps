import httpx

from tools._base import mcp, HA_URL, HEADERS, _ws


@mcp.tool()
def list_groups(search: str = "") -> list:
    """
    List all entity groups (group.* domain) with their members.

    search: optional substring filter on group name (case-insensitive)

    Returns: [{entity_id, name, state, entities: [...], all_entities: bool}]

    Note: these are logical groups (group.*) used for grouping entity states.
    For device/area grouping, use list_areas(). For light groups, use list_lights().
    """
    with httpx.Client() as client:
        r = client.get(f"{HA_URL}/api/states", headers=HEADERS, timeout=15)
        r.raise_for_status()
    groups = []
    for s in r.json():
        if not s["entity_id"].startswith("group."):
            continue
        attrs = s.get("attributes", {})
        name = attrs.get("friendly_name", s["entity_id"])
        if search and search.lower() not in name.lower():
            continue
        groups.append({
            "entity_id": s["entity_id"],
            "name": name,
            "state": s["state"],
            "entities": attrs.get("entity_id", []),
            "all_entities": attrs.get("all", False),
            "icon": attrs.get("icon", ""),
        })
    return sorted(groups, key=lambda x: x["name"])


@mcp.tool()
def create_group(
    name: str,
    entities: list,
    all_entities: bool = False,
    icon: str = "",
) -> dict:
    """
    Create or update a logical group (group.*).

    name:        group name — also used to derive the entity_id (e.g. 'Living Room Lights'
                 → 'group.living_room_lights')
    entities:    list of entity_ids to include in the group,
                 e.g. ['light.living_room', 'light.kitchen', 'switch.lamp']
    all_entities: if True, group state is 'on' only when ALL entities are on
                  (default False: 'on' when ANY entity is on)
    icon:        MDI icon, e.g. 'mdi:lightbulb-group' (optional)

    Use list_groups() after creating to verify the result.
    """
    data: dict = {
        "object_id": name.lower().replace(" ", "_"),
        "name": name,
        "entities": entities,
        "all": all_entities,
    }
    if icon:
        data["icon"] = icon
    with httpx.Client() as client:
        r = client.post(
            f"{HA_URL}/api/services/group/set",
            headers=HEADERS,
            json={
                "object_id": data["object_id"],
                "name": name,
                "entities": ",".join(entities),
                "all": all_entities,
                **({"icon": icon} if icon else {}),
            },
            timeout=15,
        )
        r.raise_for_status()
    return {
        "entity_id": f"group.{data['object_id']}",
        "name": name,
        "entities": entities,
    }


@mcp.tool()
def update_group(
    entity_id: str,
    entities: list = None,
    name: str = "",
    all_entities: bool = None,
    icon: str = "",
) -> dict:
    """
    Update an existing group's members, name, or icon.

    entity_id:   e.g. 'group.living_room_lights'
    entities:    new list of entity_ids (replaces current members)
    name:        new display name
    all_entities: change the 'all' behavior (True = all must be on, False = any)
    icon:        new MDI icon

    Only non-None/non-empty fields are updated; others keep their current value.
    """
    object_id = entity_id.removeprefix("group.")
    payload: dict = {"object_id": object_id}
    if entities is not None:
        payload["entities"] = ",".join(entities)
    if name:
        payload["name"] = name
    if all_entities is not None:
        payload["all"] = all_entities
    if icon:
        payload["icon"] = icon
    with httpx.Client() as client:
        r = client.post(
            f"{HA_URL}/api/services/group/set",
            headers=HEADERS,
            json=payload,
            timeout=15,
        )
        r.raise_for_status()
    return {"entity_id": entity_id, "updated": True}


@mcp.tool()
def delete_group(entity_id: str) -> dict:
    """
    Delete a logical group (group.*).

    entity_id: e.g. 'group.living_room_lights'. Use list_groups() to find entity_ids.

    Note: only groups created via the 'group.set' service can be deleted this way.
    YAML-defined groups (in groups.yaml) must be removed manually from the file.
    """
    object_id = entity_id.removeprefix("group.")
    with httpx.Client() as client:
        r = client.post(
            f"{HA_URL}/api/services/group/remove",
            headers=HEADERS,
            json={"object_id": object_id},
            timeout=15,
        )
        r.raise_for_status()
    return {"deleted": entity_id, "success": True}
