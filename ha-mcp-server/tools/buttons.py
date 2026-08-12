import httpx

from tools._base import mcp, HA_URL, HEADERS


@mcp.tool()
def press_button(entity_id: str) -> dict:
    """Press a button entity (domain: button or input_button)."""
    domain = entity_id.split(".")[0]
    if domain not in ("button", "input_button"):
        raise ValueError("entity_id must be a button.* or input_button.* entity")
    with httpx.Client() as client:
        r = client.post(
            f"{HA_URL}/api/services/{domain}/press",
            headers=HEADERS,
            json={"entity_id": entity_id},
            timeout=10,
        )
        r.raise_for_status()
    return {"entity_id": entity_id, "pressed": True}
