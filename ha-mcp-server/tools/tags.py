from tools._base import mcp, _ws


@mcp.tool()
def list_tags() -> list:
    """
    List all NFC tags registered in Home Assistant.

    Returns: [{id, name, last_scanned, last_scanned_by_device_id}]
    Tags can be used to trigger automations when scanned with an NFC reader or phone.
    """
    result = _ws({"type": "tag/list"})
    if not result.get("success", True):
        err = result.get("error", {})
        return [{"error": err.get("code", "unknown"), "detail": err.get("message", "")}]
    tags = result.get("result", [])
    return [
        {
            "id": t.get("id"),
            "name": t.get("name") or "",
            "last_scanned": t.get("last_scanned"),
            "last_scanned_by_device_id": t.get("last_scanned_by_device_id"),
        }
        for t in sorted(tags, key=lambda x: (x.get("name") or x.get("id", "")).lower())
    ]


@mcp.tool()
def create_tag(name: str, tag_id: str = "") -> dict:
    """
    Create a new NFC tag in Home Assistant.

    name:   friendly name for the tag, e.g. 'Front Door', 'Desk'
    tag_id: optional custom tag ID (UUID format). Leave empty to auto-generate.

    After creating, use the tag ID to configure the NFC tag with the HA Companion App
    or write it to a physical NFC sticker.
    Use create_automation() to trigger actions when the tag is scanned:
      trigger: [{"platform": "tag", "tag_id": "<id>"}]
    """
    msg: dict = {"type": "tag/create", "name": name}
    if tag_id:
        msg["tag_id"] = tag_id
    result = _ws(msg)
    if not result.get("success", True):
        err = result.get("error", {})
        return {"error": err.get("code", "unknown"), "detail": err.get("message", "")}
    return result.get("result", result)


@mcp.tool()
def update_tag(tag_id: str, name: str) -> dict:
    """
    Rename an existing NFC tag.

    tag_id: tag ID (use list_tags() to find it)
    name:   new display name
    """
    result = _ws({"type": "tag/update_tag", "tag_id": tag_id, "name": name})
    if not result.get("success", True):
        err = result.get("error", {})
        return {"error": err.get("code", "unknown"), "detail": err.get("message", "")}
    return result.get("result", {"tag_id": tag_id, "name": name})


@mcp.tool()
def delete_tag(tag_id: str) -> dict:
    """
    Delete an NFC tag.

    tag_id: tag ID (use list_tags() to find it)
    """
    result = _ws({"type": "tag/remove", "tag_id": tag_id})
    if not result.get("success", True):
        err = result.get("error", {})
        return {"error": err.get("code", "unknown"), "detail": err.get("message", "")}
    return {"deleted": tag_id, "success": True}
