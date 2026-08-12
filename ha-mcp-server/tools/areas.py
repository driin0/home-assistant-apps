import json

import httpx

from tools._base import mcp, HA_URL, HEADERS, _ws, _ws_multi


@mcp.tool()
def list_areas() -> list:
    """
    List all areas with their entities, floor name and floor_id.
    Returns: [{area_id, name, floor_id, floor_name, entities: [...]}]
    """
    ws_results = _ws_multi([
        {"type": "config/area_registry/list"},
        {"type": "config/floor_registry/list"},
    ])
    areas_raw = ws_results[0].get("result", [])
    floor_map = {f["floor_id"]: f["name"] for f in ws_results[1].get("result", [])}

    template = (
        "{%- set area_ids = areas() | list %}"
        "{%- set ns = namespace(result=[]) %}"
        "{%- for aid in area_ids %}"
        "{%- set ns.result = ns.result + [{"
        "'area_id': aid, "
        "'entities': area_entities(aid) | list"
        "}] %}"
        "{%- endfor %}"
        "{{ ns.result | tojson }}"
    )
    with httpx.Client() as client:
        r = client.post(f"{HA_URL}/api/template", headers=HEADERS,
                        json={"template": template}, timeout=15)
        r.raise_for_status()
    entities_map = {item["area_id"]: item["entities"] for item in json.loads(r.text.strip())}

    result = []
    for area in areas_raw:
        area_id = area.get("area_id", "")
        floor_id = area.get("floor_id")
        result.append({
            "area_id": area_id,
            "name": area.get("name", ""),
            "floor_id": floor_id,
            "floor_name": floor_map.get(floor_id, "") if floor_id else "",
            "entities": entities_map.get(area_id, []),
        })
    return sorted(result, key=lambda x: x["name"])


@mcp.tool()
def create_area(name: str, icon: str = "") -> dict:
    """Create a new area. icon: MDI icon, e.g. 'mdi:sofa'."""
    msg: dict = {"type": "config/area_registry/create", "name": name}
    if icon:
        msg["icon"] = icon
    r = _ws(msg)
    return r.get("result", r)


@mcp.tool()
def update_area(area_id: str, name: str = "", icon: str = "") -> dict:
    """
    Update an existing area's name and/or icon.
    Use list_areas() to find area_ids.
    """
    msg: dict = {"type": "config/area_registry/update", "area_id": area_id}
    if name:
        msg["name"] = name
    if icon:
        msg["icon"] = icon
    r = _ws(msg)
    return r.get("result", r)


@mcp.tool()
def delete_area(area_id: str) -> dict:
    """Delete an area by area_id."""
    r = _ws({"type": "config/area_registry/delete", "area_id": area_id})
    return {"deleted": area_id, "success": r.get("success", False)}


@mcp.tool()
def list_devices(area_id: str = "", search: str = "", limit: int = 50, offset: int = 0) -> dict:
    """
    List devices from the device registry with pagination.

    area_id: filter by area (use list_areas() to find IDs)
    search:  filter by name substring (case-insensitive)
    limit:   max devices to return (default 50)
    offset:  skip first N devices (for pagination)

    Returns: {total, returned, offset, devices: [{id, name, manufacturer, model, area_id, labels}]}
    """
    r = _ws({"type": "config/device_registry/list"})
    devices = r.get("result", [])
    if area_id:
        devices = [d for d in devices if d.get("area_id") == area_id]
    trimmed = [
        {
            "id": d.get("id"),
            "name": d.get("name_by_user") or d.get("name") or "",
            "manufacturer": d.get("manufacturer") or "",
            "model": d.get("model") or "",
            "area_id": d.get("area_id"),
            "labels": list(d.get("labels", [])),
        }
        for d in devices
    ]
    trimmed.sort(key=lambda x: x["name"].lower())
    if search:
        trimmed = [d for d in trimmed if search.lower() in d["name"].lower()]
    total = len(trimmed)
    page = trimmed[offset: offset + limit]
    return {"total": total, "returned": len(page), "offset": offset, "devices": page}


@mcp.tool()
def get_device(device_id: str) -> dict:
    """Get full details of a device by device_id."""
    r = _ws({"type": "config/device_registry/list"})
    for d in r.get("result", []):
        if d.get("id") == device_id:
            return d
    return {"error": f"Device not found: {device_id}"}


@mcp.tool()
def rename_entity(entity_id: str, name: str) -> dict:
    """
    Set a custom display name for an entity (overrides the default name).
    Pass name='' to reset to the original integration-provided name.
    """
    r = _ws({
        "type": "config/entity_registry/update",
        "entity_id": entity_id,
        "name": name or None,
    })
    entry = r.get("result", {}).get("entity_entry", {})
    return {
        "entity_id": entity_id,
        "name": entry.get("name") or entry.get("original_name", ""),
        "success": r.get("success", False),
    }


@mcp.tool()
def list_labels() -> dict:
    """List all labels defined in Home Assistant, sorted by name."""
    r = _ws({"type": "config/label_registry/list"})
    labels = sorted(r.get("result", []), key=lambda x: x.get("name", "").lower())
    return {"total": len(labels), "labels": labels}


@mcp.tool()
def create_label(name: str, color: str = "", icon: str = "") -> dict:
    """
    Create a new label.

    color: CSS color string, e.g. '#ff5733' or 'red'
    icon:  MDI icon, e.g. 'mdi:star'
    """
    msg: dict = {"type": "config/label_registry/create", "name": name}
    if color:
        msg["color"] = color
    if icon:
        msg["icon"] = icon
    r = _ws(msg)
    return r.get("result", r)


@mcp.tool()
def update_label(label_id: str, name: str = "", color: str = "", icon: str = "") -> dict:
    """
    Update an existing label's name, color and/or icon.

    label_id: the label to update (use list_labels() to find it)
    name:     new display name (leave empty to keep current)
    color:    CSS color string, e.g. '#ff5733' or 'red'
    icon:     MDI icon, e.g. 'mdi:star'
    """
    msg: dict = {"type": "config/label_registry/update", "label_id": label_id}
    if name:
        msg["name"] = name
    if color:
        msg["color"] = color
    if icon:
        msg["icon"] = icon
    r = _ws(msg)
    return r.get("result", r)


@mcp.tool()
def delete_label(label_id: str) -> dict:
    """Delete a label by label_id."""
    r = _ws({"type": "config/label_registry/delete", "label_id": label_id})
    return {"deleted": label_id, "success": r.get("success", False)}


@mcp.tool()
def get_entity_labels(entity_id: str) -> list:
    """Get the labels currently assigned to an entity."""
    r = _ws({"type": "config/entity_registry/get", "entity_id": entity_id})
    return list(r.get("result", {}).get("labels", []))


@mcp.tool()
def set_entity_labels(entity_id: str, labels: list) -> dict:
    """
    Set labels on an entity (replaces existing labels).

    labels: list of label_id strings, e.g. ["energia", "illuminazione"]
    Use list_labels() to discover available label IDs.
    """
    r = _ws({
        "type": "config/entity_registry/update",
        "entity_id": entity_id,
        "labels": labels,
    })
    entry = r.get("result", {}).get("entity_entry", {})
    return {
        "entity_id": entity_id,
        "labels": list(entry.get("labels", labels)),
        "success": r.get("success", False),
    }


@mcp.tool()
def bulk_set_entity_labels(entity_ids: list, labels: list) -> dict:
    """
    Assign labels to multiple entities at once (replaces existing labels on each entity).

    entity_ids: list of entity_id strings
    labels: list of label_id strings to assign to all entities

    Returns: {total, succeeded, failed: [...]}
    """
    msgs = [
        {"type": "config/entity_registry/update", "entity_id": eid, "labels": labels}
        for eid in entity_ids
    ]
    results = _ws_multi(msgs)
    succeeded, failed = 0, []
    for eid, r in zip(entity_ids, results):
        if r.get("success"):
            succeeded += 1
        else:
            failed.append(eid)
    return {"total": len(entity_ids), "succeeded": succeeded, "failed": failed}


@mcp.tool()
def list_floors() -> dict:
    """List all floors defined in Home Assistant, sorted by level."""
    r = _ws({"type": "config/floor_registry/list"})
    floors = sorted(r.get("result", []), key=lambda x: x.get("level", 0))
    return {"total": len(floors), "floors": floors}


@mcp.tool()
def create_floor(name: str, level: int = 0, icon: str = "") -> dict:
    """
    Create a new floor.

    level: integer floor level (0 = ground floor, 1 = first floor, -1 = basement, …)
    icon:  MDI icon, e.g. 'mdi:home-floor-0'
    """
    msg: dict = {"type": "config/floor_registry/create", "name": name, "level": level}
    if icon:
        msg["icon"] = icon
    r = _ws(msg)
    return r.get("result", r)


@mcp.tool()
def delete_floor(floor_id: str) -> dict:
    """Delete a floor by floor_id."""
    r = _ws({"type": "config/floor_registry/delete", "floor_id": floor_id})
    return {"deleted": floor_id, "success": r.get("success", False)}


@mcp.tool()
def get_entity_registry(entity_id: str) -> dict:
    """
    Get full entity registry info for an entity: area, platform, unique_id,
    disabled_by, hidden_by, aliases, icon, device_id, and more.

    Useful for diagnosing entity configuration or finding the device an entity belongs to.
    """
    r = _ws({"type": "config/entity_registry/get", "entity_id": entity_id})
    result = r.get("result") or {}
    return {
        "entity_id": result.get("entity_id"),
        "name": result.get("name") or result.get("original_name"),
        "platform": result.get("platform"),
        "device_id": result.get("device_id"),
        "area_id": result.get("area_id"),
        "unique_id": result.get("unique_id"),
        "disabled_by": result.get("disabled_by"),
        "hidden_by": result.get("hidden_by"),
        "icon": result.get("icon") or result.get("original_icon"),
        "labels": list(result.get("labels", [])),
        "aliases": list(result.get("aliases", [])),
        "has_entity_name": result.get("has_entity_name", False),
    }


@mcp.tool()
def list_zones() -> list:
    """
    List all zone entities (home, work, school, etc.) with GPS coordinates and radius.
    Zones are used for presence detection and location-based automations.
    """
    with httpx.Client() as client:
        r = client.get(f"{HA_URL}/api/states", headers=HEADERS, timeout=15)
        r.raise_for_status()
        zones = []
        for s in r.json():
            if not s["entity_id"].startswith("zone."):
                continue
            attrs = s.get("attributes", {})
            zones.append({
                "entity_id": s["entity_id"],
                "name": attrs.get("friendly_name", s["entity_id"]),
                "latitude": attrs.get("latitude"),
                "longitude": attrs.get("longitude"),
                "radius": attrs.get("radius"),
                "icon": attrs.get("icon", ""),
                "passive": attrs.get("passive", False),
            })
    return sorted(zones, key=lambda x: x["name"])


@mcp.tool()
def disable_entity(entity_id: str) -> dict:
    """
    Disable an entity in the entity registry.
    Disabled entities are hidden from HA and stop reporting state.
    Use enable_entity() to re-enable.
    """
    r = _ws({
        "type": "config/entity_registry/update",
        "entity_id": entity_id,
        "disabled_by": "user",
    })
    return {"entity_id": entity_id, "disabled": True, "success": r.get("success", False)}


@mcp.tool()
def enable_entity(entity_id: str) -> dict:
    """
    Re-enable a previously disabled entity in the entity registry.
    """
    r = _ws({
        "type": "config/entity_registry/update",
        "entity_id": entity_id,
        "disabled_by": None,
    })
    return {"entity_id": entity_id, "enabled": True, "success": r.get("success", False)}


@mcp.tool()
def set_area_floor(area_id: str, floor_id: str) -> dict:
    """
    Assign an area to a floor (pass floor_id='' to remove the assignment).
    Use list_areas() for area_ids and list_floors() for floor_ids.
    """
    r = _ws({
        "type": "config/area_registry/update",
        "area_id": area_id,
        "floor_id": floor_id or None,
    })
    entry = r.get("result", {})
    return {
        "area_id": area_id,
        "floor_id": entry.get("floor_id"),
        "success": r.get("success", False),
    }


@mcp.tool()
def set_entity_area(entity_id: str, area_id: str) -> dict:
    """
    Assign an entity to an area (or remove it from any area).

    entity_id: entity to update, e.g. 'light.living_room'
    area_id:   area to assign it to (use list_areas() to find IDs).
               Pass '' (empty string) to remove the entity from its current area.

    Note: this overrides the device-level area for this specific entity.
    """
    r = _ws({
        "type": "config/entity_registry/update",
        "entity_id": entity_id,
        "area_id": area_id or None,
    })
    entry = r.get("result", {}).get("entity_entry", {})
    return {
        "entity_id": entity_id,
        "area_id": entry.get("area_id"),
        "success": r.get("success", False),
    }
