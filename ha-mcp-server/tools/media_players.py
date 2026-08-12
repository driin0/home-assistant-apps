import httpx

from tools._base import mcp, HA_URL, HEADERS, ALEXA_KEYWORDS, default_language, _ws


@mcp.tool()
def list_media_players() -> list:
    """List all media player entities with current state."""
    with httpx.Client() as client:
        r = client.get(f"{HA_URL}/api/states", headers=HEADERS, timeout=15)
        r.raise_for_status()
        result = []
        for s in r.json():
            if not s["entity_id"].startswith("media_player."):
                continue
            attrs = s.get("attributes", {})
            result.append({
                "entity_id": s["entity_id"],
                "name": attrs.get("friendly_name", s["entity_id"]),
                "state": s["state"],
                "media_title": attrs.get("media_title"),
                "media_artist": attrs.get("media_artist"),
                "volume_level": attrs.get("volume_level"),
                "is_volume_muted": attrs.get("is_volume_muted"),
                "source": attrs.get("source"),
                "source_list": attrs.get("source_list", []),
            })
        return sorted(result, key=lambda x: x["name"])


@mcp.tool()
def send_tts(entity_id: str, message: str, language: str = "", engine: str = "tts.google_translate") -> dict:
    """
    Send a text-to-speech announcement to a media player.

    entity_id: media_player entity (e.g. 'media_player.echo_living_room')
    message: text to speak
    language: language code; defaults to the language configured in Home Assistant
    engine: TTS engine entity_id for non-Alexa players (default: 'tts.google_translate').
            Options: 'tts.cloud' (HA Cloud), 'tts.google_translate', 'tts.piper'

    For Amazon Echo (Alexa Media Player integration), uses alexa_media announce
    automatically. A player counts as an Echo when its entity_id contains one of
    the configured Alexa keywords ('echo' or 'alexa' unless changed) — set them
    to match speaker groups named after a room or the household.
    """
    language = language or default_language()
    name = entity_id.split(".", 1)[1]
    is_alexa = any(kw in name.lower() for kw in ALEXA_KEYWORDS)

    with httpx.Client() as client:
        if is_alexa:
            notify_service = f"alexa_media_{name}"
            r = client.post(
                f"{HA_URL}/api/services/notify/{notify_service}",
                headers=HEADERS,
                json={"message": message, "data": {"type": "announce"}},
                timeout=15,
            )
        else:
            r = client.post(
                f"{HA_URL}/api/services/tts/speak",
                headers=HEADERS,
                json={
                    "entity_id": engine,
                    "media_player_entity_id": entity_id,
                    "message": message,
                    "language": language,
                    "cache": False,
                },
                timeout=15,
            )
        r.raise_for_status()
    return {"entity_id": entity_id, "message": message, "method": "alexa_announce" if is_alexa else "tts_speak"}


@mcp.tool()
def media_player_control(
    entity_id: str,
    command: str,
    volume: float = None,
    source: str = "",
    media_content_id: str = "",
    media_content_type: str = "music",
) -> dict:
    """
    Control a media player.

    command:
      - 'play'        resume playback
      - 'pause'       pause playback
      - 'stop'        stop playback
      - 'next'        next track
      - 'previous'    previous track
      - 'turn_on'     turn on
      - 'turn_off'    turn off
      - 'mute'        toggle mute
      - 'volume'      set volume (requires volume: 0.0–1.0)
      - 'source'      select source (requires source parameter)
      - 'play_media'  play specific media (requires media_content_id, optional media_content_type)
    """
    cmd_map = {
        "play": "media_play", "pause": "media_pause", "stop": "media_stop",
        "next": "media_next_track", "previous": "media_previous_track",
        "turn_on": "turn_on", "turn_off": "turn_off", "mute": "toggle",
    }
    with httpx.Client() as client:
        if command in cmd_map:
            r = client.post(f"{HA_URL}/api/services/media_player/{cmd_map[command]}",
                            headers=HEADERS, json={"entity_id": entity_id}, timeout=10)
        elif command == "volume" and volume is not None:
            r = client.post(f"{HA_URL}/api/services/media_player/volume_set",
                            headers=HEADERS,
                            json={"entity_id": entity_id, "volume_level": volume}, timeout=10)
        elif command == "source" and source:
            r = client.post(f"{HA_URL}/api/services/media_player/select_source",
                            headers=HEADERS,
                            json={"entity_id": entity_id, "source": source}, timeout=10)
        elif command == "play_media" and media_content_id:
            r = client.post(f"{HA_URL}/api/services/media_player/play_media",
                            headers=HEADERS,
                            json={
                                "entity_id": entity_id,
                                "media_content_id": media_content_id,
                                "media_content_type": media_content_type,
                            }, timeout=10)
        else:
            return {"error": f"Unknown command or missing parameters: {command}"}
        r.raise_for_status()
        return {"command": command, "entity_id": entity_id, "ok": True}


@mcp.tool()
def search_and_play_media(entity_id: str, query: str, media_type: str = "music") -> dict:
    """
    Search for media and play it on a media player.

    entity_id: target media player (e.g. 'media_player.spotify')
    query: search query (e.g. 'Daft Punk', 'Bohemian Rhapsody')
    media_type: content type hint — 'music', 'playlist', 'podcast', 'video' (default: 'music')

    Works on players that support media browsing/search (Spotify, YouTube Music, etc.).
    Uses the HA media_player.play_media service with enqueue=replace.
    """
    with httpx.Client() as client:
        r = client.post(
            f"{HA_URL}/api/services/media_player/play_media",
            headers=HEADERS,
            json={
                "entity_id": entity_id,
                "media_content_id": query,
                "media_content_type": media_type,
                "enqueue": "replace",
            },
            timeout=15,
        )
        r.raise_for_status()
    return {"entity_id": entity_id, "query": query, "media_type": media_type, "ok": True}


@mcp.tool()
def broadcast_tts(message: str, language: str = "", engine: str = "tts.google_translate") -> dict:
    """
    Send a TTS announcement to all active media players simultaneously.

    Alexa/Echo devices use alexa_media announce automatically.
    All other active media players use the specified TTS engine.

    message: text to speak
    language: language code; defaults to the language configured in Home Assistant
    engine: TTS engine for non-Alexa players (default: 'tts.google_translate')
    """
    language = language or default_language()
    with httpx.Client() as client:
        r = client.get(f"{HA_URL}/api/states", headers=HEADERS, timeout=15)
        r.raise_for_status()
        players = [
            s for s in r.json()
            if s["entity_id"].startswith("media_player.") and s["state"] not in ("unavailable", "unknown")
        ]

    results = []

    with httpx.Client() as client:
        for player in players:
            entity_id = player["entity_id"]
            name = entity_id.split(".", 1)[1]
            is_alexa = any(kw in name.lower() for kw in ALEXA_KEYWORDS)
            try:
                if is_alexa:
                    notify_service = f"alexa_media_{name}"
                    r = client.post(
                        f"{HA_URL}/api/services/notify/{notify_service}",
                        headers=HEADERS,
                        json={"message": message, "data": {"type": "announce"}},
                        timeout=15,
                    )
                else:
                    r = client.post(
                        f"{HA_URL}/api/services/tts/speak",
                        headers=HEADERS,
                        json={
                            "entity_id": engine,
                            "media_player_entity_id": entity_id,
                            "message": message,
                            "language": language,
                            "cache": False,
                        },
                        timeout=15,
                    )
                results.append({"entity_id": entity_id, "ok": r.is_success, "method": "alexa_announce" if is_alexa else "tts_speak"})
            except Exception as e:
                results.append({"entity_id": entity_id, "ok": False, "error": str(e)})

    return {"message": message, "players": results}


@mcp.tool()
def browse_media(
    entity_id: str,
    media_content_type: str = "",
    media_content_id: str = "",
) -> dict:
    """
    Browse the media library of a media player (Spotify, Plex, YouTube Music, etc.).

    entity_id:         media player to browse, e.g. 'media_player.spotify'
    media_content_type: type of content to browse — leave empty for root level.
                        Examples: 'playlist', 'album', 'artist', 'library', 'favorites'
    media_content_id:  ID of the item to browse into (from a previous browse result).
                       Leave empty to browse the root library.

    Returns the available children (playlists, albums, tracks, etc.) for the given level.
    Use the returned children's media_content_type and media_content_id to browse deeper,
    or pass them to search_and_play_media() to start playback.
    """
    msg: dict = {"type": "media_player/browse_media", "entity_id": entity_id}
    if media_content_type:
        msg["media_content_type"] = media_content_type
    if media_content_id:
        msg["media_content_id"] = media_content_id
    result = _ws(msg)
    if not result.get("success", True):
        err = result.get("error", {})
        return {"error": err.get("code", "unknown"), "detail": err.get("message", "")}
    data = result.get("result", {})
    return {
        "title": data.get("title"),
        "media_content_type": data.get("media_content_type"),
        "media_content_id": data.get("media_content_id"),
        "can_play": data.get("can_play", False),
        "can_expand": data.get("can_expand", False),
        "children_media_class": data.get("children_media_class"),
        "children": [
            {
                "title": c.get("title"),
                "media_content_type": c.get("media_content_type"),
                "media_content_id": c.get("media_content_id"),
                "can_play": c.get("can_play", False),
                "can_expand": c.get("can_expand", False),
                "thumbnail": c.get("thumbnail"),
            }
            for c in (data.get("children") or [])
        ],
    }
