import re

import httpx

from tools._base import mcp, HA_URL, HEADERS, _ws


def _resolve_telegram_chat_id(entity_id: str) -> int:
    """
    Resolve the Telegram chat_id for a notify entity.

    Strategy:
    1. Query entity registry via WS → extract chat_id from unique_id
       (new-style telegram_bot entities: unique_id = "{bot_id}_{chat_id}")
    2. Fallback: regex on friendly_name for "(chat_id)" suffix
       (legacy YAML-configured entities and group chats)

    Raises ValueError if chat_id cannot be determined.

    TODO HA 2026.9.0: migrate callers to use 'chat_id' or 'entity_id' parameter
    directly in telegram_bot service calls once the new API is stable.
    """
    # 1. Entity registry unique_id
    reg = _ws({"type": "config/entity_registry/get", "entity_id": entity_id})
    unique_id = (reg.get("result") or {}).get("unique_id") or ""
    if unique_id:
        # Format: "{bot_id}_{chat_id}" — split on first underscore-separated bot_id
        parts = unique_id.split("_", 1)
        if len(parts) == 2 and parts[1].lstrip("-").isdigit():
            return int(parts[1])

    # 2. Fallback: friendly_name "(chat_id)" suffix
    with httpx.Client() as client:
        r = client.get(f"{HA_URL}/api/states/{entity_id}", headers=HEADERS, timeout=10)
        if r.status_code == 200:
            friendly = r.json().get("attributes", {}).get("friendly_name", "")
            m = re.search(r"\((-?\d+)\)\s*$", friendly)
            if m:
                return int(m.group(1))

    raise ValueError(
        f"Cannot resolve Telegram chat_id for {entity_id}. "
        "Add the chat_id in parentheses to the entity's friendly name, e.g. 'Name (123456)'."
    )


def _telegram_type(chat_id: int | None) -> str:
    """Infer Telegram target type from chat_id."""
    if chat_id is None:
        return "other"
    if chat_id > 0:
        return "telegram_private"
    return "telegram_group"  # negative: group or channel


@mcp.tool()
def list_notify_services() -> list:
    """
    List all available notification services with entity_id, friendly_name and type.
    type: 'telegram_private', 'telegram_group', or 'other' (mobile app, Alexa, file, etc.)
    Includes Telegram targets, mobile app, Alexa and other notify entities.
    """
    with httpx.Client() as client:
        r = client.get(f"{HA_URL}/api/states", headers=HEADERS, timeout=15)
        r.raise_for_status()
        results = []
        for entity in r.json():
            if not entity.get("entity_id", "").startswith("notify."):
                continue
            friendly = entity.get("attributes", {}).get("friendly_name", "")
            m = re.search(r"\((-?\d+)\)\s*$", friendly)
            chat_id = int(m.group(1)) if m else None
            results.append({
                "entity_id": entity["entity_id"],
                "name": friendly,
                "type": _telegram_type(chat_id),
                "state": entity.get("state"),
            })
        return sorted(results, key=lambda x: x["entity_id"])


@mcp.tool()
def send_notification(message: str, title: str = "", target: str = "notify.notify") -> dict:
    """
    Send a notification to a notify entity.

    target: entity_id of the notify target (e.g. 'notify.telegram_home', 'notify.mobile_app_myphone').
            Use list_notify_services() to discover available targets.
    """
    entity_id = target if target.startswith("notify.") else f"notify.{target}"
    data: dict = {"message": message}
    if title:
        data["title"] = title
    with httpx.Client() as client:
        r = client.post(
            f"{HA_URL}/api/services/notify/send_message",
            headers=HEADERS,
            json={"entity_id": entity_id, **data},
            timeout=15,
        )
        r.raise_for_status()
        return {"sent": True, "target": entity_id, "message": message}


@mcp.tool()
def send_notification_with_buttons(
    target: str,
    message: str,
    buttons: list,
    title: str = "",
) -> dict:
    """
    Send a Telegram message with inline keyboard buttons.

    target: notify entity_id (e.g. 'notify.telegram_home')
    buttons: list of button rows. Each row is a list of button dicts.
      - URL button:  {"text": "Open", "url": "https://..."}
      - Callback:    {"text": "Yes", "callback_data": "/yes"}

    Example:
      buttons: [[{"text": "Open HA", "url": "https://homeassistant.local:8123"}]]
      buttons: [[{"text": "Yes", "callback_data": "/yes"}, {"text": "No", "callback_data": "/no"}]]
    """
    entity_id = target if target.startswith("notify.") else f"notify.{target}"
    payload: dict = {
        "entity_id": entity_id,
        "message": message,
        "data": {"inline_keyboard": buttons},
    }
    if title:
        payload["title"] = title
    with httpx.Client() as client:
        r = client.post(
            f"{HA_URL}/api/services/notify/send_message",
            headers=HEADERS,
            json=payload,
            timeout=15,
        )
        r.raise_for_status()
        return {"sent": True, "target": entity_id, "message": message}


@mcp.tool()
def send_photo(target: str, photo_url: str, caption: str = "") -> dict:
    """
    Send a photo via Telegram using telegram_bot.send_photo.

    target: notify entity_id (e.g. 'notify.telegram_home')
    photo_url: publicly accessible direct URL of the photo (no redirects)
    caption: optional caption text
    """
    entity_id = target if target.startswith("notify.") else f"notify.{target}"
    chat_id = _resolve_telegram_chat_id(entity_id)
    payload: dict = {"url": photo_url, "target": [chat_id]}
    if caption:
        payload["caption"] = caption
    with httpx.Client() as client:
        r = client.post(
            f"{HA_URL}/api/services/telegram_bot/send_photo",
            headers=HEADERS,
            json=payload,
            timeout=15,
        )
        r.raise_for_status()
        return {"sent": True, "target": entity_id, "chat_id": chat_id, "photo": photo_url}


@mcp.tool()
def send_camera_snapshot(camera_entity_id: str, target: str, caption: str = "") -> dict:
    """
    Fetch a camera snapshot and send it to a Telegram chat.

    Uses the camera entity's access_token to build a public URL (no Bearer auth needed),
    then sends it via telegram_bot.send_photo. Requires HA to have an external_url configured
    (Settings → System → Network → Home Assistant URL).

    camera_entity_id: e.g. 'camera.gate_snapshot'
    target: notify entity_id (e.g. 'notify.telegram_home')
    caption: optional caption text
    """
    # 1. Resolve chat_id
    notify_id = target if target.startswith("notify.") else f"notify.{target}"
    chat_id = _resolve_telegram_chat_id(notify_id)

    with httpx.Client() as client:
        # 2. Get camera access_token from entity state
        r = client.get(f"{HA_URL}/api/states/{camera_entity_id}", headers=HEADERS, timeout=10)
        if r.status_code == 404:
            return {"error": "not_found", "entity_id": camera_entity_id, "detail": "Camera entity not found."}
        r.raise_for_status()
        access_token = r.json().get("attributes", {}).get("access_token")
        if not access_token:
            return {"error": "no_access_token", "entity_id": camera_entity_id,
                    "detail": "Camera entity has no access_token attribute."}

        # 3. Get HA external URL
        cfg = client.get(f"{HA_URL}/api/config", headers=HEADERS, timeout=10)
        cfg.raise_for_status()
        cfg_data = cfg.json()
        external_url = cfg_data.get("external_url") or cfg_data.get("internal_url", "")
        if not external_url:
            return {"error": "no_external_url", "detail": "Set an external URL in HA Settings → System → Network."}

        external_url = external_url.rstrip("/")

        # 4. Build token-authenticated URL (no Bearer auth required — Telegram can fetch it)
        photo_url = f"{external_url}/api/camera_proxy/{camera_entity_id}?token={access_token}"

        # 5. Send via telegram_bot.send_photo
        payload: dict = {"url": photo_url, "target": [chat_id]}
        if caption:
            payload["caption"] = caption
        r = client.post(
            f"{HA_URL}/api/services/telegram_bot/send_photo",
            headers=HEADERS,
            json=payload,
            timeout=15,
        )
        r.raise_for_status()

    return {
        "sent": True,
        "camera": camera_entity_id,
        "target": notify_id,
        "chat_id": chat_id,
        "photo_url": photo_url,
    }


@mcp.tool()
def create_persistent_notification(message: str, title: str = "", notification_id: str = "") -> dict:
    """
    Create a persistent notification in the Home Assistant UI.

    notification_id: optional — if provided, a subsequent call with the same ID
                     will update the existing notification instead of creating a new one.
    """
    data: dict = {"message": message}
    if title:
        data["title"] = title
    if notification_id:
        data["notification_id"] = notification_id
    with httpx.Client() as client:
        r = client.post(
            f"{HA_URL}/api/services/persistent_notification/create",
            headers=HEADERS,
            json=data,
            timeout=10,
        )
        r.raise_for_status()
    return {"created": True, "notification_id": notification_id or None, "title": title, "message": message}


@mcp.tool()
def list_persistent_notifications() -> list:
    """List all active persistent notifications in Home Assistant."""
    result = _ws({"type": "persistent_notification/get"})
    notifications = result.get("result", [])
    return [
        {
            "notification_id": n.get("notification_id"),
            "title": n.get("title", ""),
            "message": n.get("message", ""),
            "created_at": n.get("created_at"),
        }
        for n in notifications
    ]


@mcp.tool()
def dismiss_persistent_notification(notification_id: str) -> dict:
    """Dismiss a persistent notification by its notification_id."""
    with httpx.Client() as client:
        r = client.post(
            f"{HA_URL}/api/services/persistent_notification/dismiss",
            headers=HEADERS,
            json={"notification_id": notification_id},
            timeout=10,
        )
        r.raise_for_status()
    return {"dismissed": True, "notification_id": notification_id}
