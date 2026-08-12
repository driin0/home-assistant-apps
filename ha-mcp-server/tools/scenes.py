import httpx

from tools._base import mcp, HA_URL, HEADERS, _slug


@mcp.tool()
def list_scenes() -> list:
    """List all scenes with their entity list and current states."""
    with httpx.Client() as client:
        states_r = client.get(f"{HA_URL}/api/states", headers=HEADERS, timeout=15)
        states_r.raise_for_status()
        all_states = {s["entity_id"]: s["state"] for s in states_r.json()}
        scenes = []
        for s in states_r.json():
            if not s["entity_id"].startswith("scene."):
                continue
            attrs = s.get("attributes", {})
            entity_ids = attrs.get("entity_id", [])
            scenes.append({
                "entity_id": s["entity_id"],
                "name": attrs.get("friendly_name", s["entity_id"]),
                "entities": {eid: all_states.get(eid, "unknown") for eid in entity_ids},
            })
        return sorted(scenes, key=lambda x: x["name"])


@mcp.tool()
def activate_scene(entity_id: str) -> dict:
    """Activate a scene by entity_id (e.g. 'scene.movie_night')."""
    with httpx.Client() as client:
        r = client.post(
            f"{HA_URL}/api/services/scene/turn_on",
            headers=HEADERS,
            json={"entity_id": entity_id},
            timeout=10,
        )
        r.raise_for_status()
        return {"activated": entity_id}


@mcp.tool()
def create_scene(name: str, entities: dict) -> dict:
    """
    Create or update a scene.

    entities: dict of entity_id -> state/attributes to capture.

    Example — a cinema scene:
      name: "Cinema"
      entities: {
        "light.living_room": {"state": "on", "brightness": 30},
        "switch.living_room_night_light": {"state": "on"}
      }
    """
    scene_id = _slug(name)
    payload = {
        "name": name,
        "entities": entities,
    }
    with httpx.Client() as client:
        r = client.post(
            f"{HA_URL}/api/config/scene/config/{scene_id}",
            headers=HEADERS,
            json=payload,
            timeout=15,
        )
        r.raise_for_status()
        return {"scene_id": scene_id, "entity_id": f"scene.{scene_id}", "result": r.json()}


@mcp.tool()
def delete_scene(entity_id: str) -> dict:
    """Delete a scene by entity_id (e.g. 'scene.cinema')."""
    scene_id = entity_id.removeprefix("scene.")
    with httpx.Client() as client:
        r = client.delete(
            f"{HA_URL}/api/config/scene/config/{scene_id}",
            headers=HEADERS,
            timeout=10,
        )
        r.raise_for_status()
        return {"deleted": entity_id, "status": r.status_code}
