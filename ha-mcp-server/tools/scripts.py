import httpx

from tools._base import mcp, HA_URL, HEADERS, _slug


@mcp.tool()
def list_scripts() -> list:
    """List all scripts with their state (on = running, off = idle)."""
    with httpx.Client() as client:
        r = client.get(f"{HA_URL}/api/states", headers=HEADERS, timeout=15)
        r.raise_for_status()
        scripts = [
            {
                "entity_id": s["entity_id"],
                "name": s.get("attributes", {}).get("friendly_name", s["entity_id"]),
                "state": s["state"],
            }
            for s in r.json()
            if s["entity_id"].startswith("script.")
        ]
        return sorted(scripts, key=lambda x: x["name"])


@mcp.tool()
def run_script(entity_id: str, variables: dict = None) -> dict:
    """
    Run a script by entity_id (e.g. 'script.restart_mqtt_broker').
    Optionally pass variables as a dict.
    """
    data = {"entity_id": entity_id}
    if variables:
        data["variables"] = variables
    with httpx.Client() as client:
        r = client.post(
            f"{HA_URL}/api/services/script/turn_on",
            headers=HEADERS,
            json=data,
            timeout=15,
        )
        r.raise_for_status()
        return {"triggered": entity_id}


@mcp.tool()
def create_script(name: str, sequence: list, description: str = "") -> dict:
    """
    Create or update a script.

    Example — script that turns off all lights:
      name: "Turn everything off"
      sequence: [{"service": "light.turn_off", "target": {"entity_id": "all"}}]
    """
    script_id = _slug(name)
    payload = {
        "alias": name,
        "description": description,
        "sequence": sequence,
        "mode": "single",
    }
    with httpx.Client() as client:
        r = client.post(
            f"{HA_URL}/api/config/script/config/{script_id}",
            headers=HEADERS,
            json=payload,
            timeout=15,
        )
        r.raise_for_status()
        return {"script_id": script_id, "entity_id": f"script.{script_id}", "result": r.json()}


@mcp.tool()
def delete_script(entity_id: str) -> dict:
    """Delete a script by entity_id (e.g. 'script.turn_everything_off')."""
    script_id = entity_id.removeprefix("script.")
    with httpx.Client() as client:
        r = client.delete(
            f"{HA_URL}/api/config/script/config/{script_id}",
            headers=HEADERS,
            timeout=10,
        )
        r.raise_for_status()
        return {"deleted": entity_id, "status": r.status_code}


@mcp.tool()
def get_script(entity_id: str) -> dict:
    """
    Get the full config (sequence, mode, description) of a script by entity_id.
    Works for scripts managed via the HA UI editor.
    """
    script_id = entity_id.removeprefix("script.")
    with httpx.Client() as client:
        r = client.get(
            f"{HA_URL}/api/config/script/config/{script_id}",
            headers=HEADERS,
            timeout=10,
        )
        if r.status_code == 404:
            return {
                "error": "not_found",
                "entity_id": entity_id,
                "detail": "Script not found via HA config API.",
            }
        r.raise_for_status()
        return r.json()
