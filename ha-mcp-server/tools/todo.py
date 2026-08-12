import httpx

from tools._base import mcp, HA_URL, HEADERS, _ws


@mcp.tool()
def list_todo_lists() -> list:
    """List all todo list entities."""
    with httpx.Client() as client:
        r = client.get(f"{HA_URL}/api/states", headers=HEADERS, timeout=15)
        r.raise_for_status()
    return [
        {
            "entity_id": s["entity_id"],
            "name": s.get("attributes", {}).get("friendly_name", s["entity_id"]),
            "item_count": s.get("attributes", {}).get("todo_items"),
        }
        for s in r.json()
        if s["entity_id"].startswith("todo.")
    ]


@mcp.tool()
def get_todo_items(entity_id: str) -> list:
    """Get all items from a todo list. entity_id: e.g. 'todo.shopping_list'"""
    result = _ws({
        "type": "call_service",
        "domain": "todo",
        "service": "get_items",
        "service_data": {"entity_id": entity_id},
        "return_response": True,
    })
    # Response result: {"response": {"todo.shopping_list": {"items": [...]}}}
    response = (result.get("result") or {}).get("response", {})
    return response.get(entity_id, {}).get("items", [])


@mcp.tool()
def add_todo_item(entity_id: str, item: str, description: str = "", due_date: str = "") -> dict:
    """
    Add an item to a todo list.

    entity_id: e.g. 'todo.shopping_list'
    item: item summary/name
    description: optional longer description
    due_date: optional due date in YYYY-MM-DD format
    """
    data: dict = {"entity_id": entity_id, "item": item}
    if description:
        data["description"] = description
    if due_date:
        data["due_date"] = due_date
    with httpx.Client() as client:
        r = client.post(
            f"{HA_URL}/api/services/todo/add_item",
            headers=HEADERS,
            json=data,
            timeout=10,
        )
        r.raise_for_status()
    return {"added": True, "entity_id": entity_id, "item": item}


@mcp.tool()
def update_todo_item(entity_id: str, item: str, status: str = "", rename: str = "") -> dict:
    """
    Update a todo item's status or name.

    entity_id: e.g. 'todo.shopping_list'
    item: current item name (uid or summary)
    status: needs_action | completed
    rename: new name for the item
    """
    data: dict = {"entity_id": entity_id, "item": item}
    if status:
        data["status"] = status
    if rename:
        data["rename"] = rename
    with httpx.Client() as client:
        r = client.post(
            f"{HA_URL}/api/services/todo/update_item",
            headers=HEADERS,
            json=data,
            timeout=10,
        )
        r.raise_for_status()
    return {"updated": True, "entity_id": entity_id, "item": item}


@mcp.tool()
def remove_todo_item(entity_id: str, item: str) -> dict:
    """Remove an item from a todo list. item: item name or uid."""
    with httpx.Client() as client:
        r = client.post(
            f"{HA_URL}/api/services/todo/remove_item",
            headers=HEADERS,
            json={"entity_id": entity_id, "item": item},
            timeout=10,
        )
        r.raise_for_status()
    return {"removed": True, "entity_id": entity_id, "item": item}
