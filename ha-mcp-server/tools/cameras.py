import base64

import httpx

from tools._base import mcp, HA_URL, HEADERS


@mcp.tool()
def list_cameras() -> list:
    """List all camera entities."""
    with httpx.Client() as client:
        r = client.get(f"{HA_URL}/api/states", headers=HEADERS, timeout=15)
        r.raise_for_status()
    cameras = []
    for s in r.json():
        if not s["entity_id"].startswith("camera."):
            continue
        attrs = s.get("attributes", {})
        cameras.append({
            "entity_id": s["entity_id"],
            "name": attrs.get("friendly_name", s["entity_id"]),
            "state": s["state"],
            "model": attrs.get("model_name") or attrs.get("model"),
        })
    return sorted(cameras, key=lambda x: x["name"])


@mcp.tool()
def get_camera_snapshot(entity_id: str) -> dict:
    """
    Fetch the latest snapshot from a camera and return it as a base64-encoded JPEG.
    entity_id: e.g. 'camera.front_door'

    Note: snapshots can be large. For offline/unavailable cameras the request will fail.
    """
    with httpx.Client() as client:
        r = client.get(
            f"{HA_URL}/api/camera_proxy/{entity_id}",
            headers=HEADERS,
            timeout=20,
        )
        if r.status_code == 404:
            return {"error": "not_found", "entity_id": entity_id, "detail": "Camera entity not found."}
        if r.status_code != 200:
            return {"error": f"http_{r.status_code}", "entity_id": entity_id}
        content_type = r.headers.get("content-type", "image/jpeg")
        image_b64 = base64.b64encode(r.content).decode("utf-8")
    return {
        "entity_id": entity_id,
        "content_type": content_type,
        "size_bytes": len(r.content),
        "image_base64": image_b64,
    }
