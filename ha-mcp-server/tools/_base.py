import asyncio
import json
import os
import re

from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer

load_dotenv()

HA_URL = os.getenv("HA_URL", "").rstrip("/")
HA_TOKEN = os.getenv("HA_TOKEN", "")
MCP_PORT = int(os.getenv("MCP_PORT", "47821"))
MCP_SECRET = os.getenv("MCP_SECRET", "")
MCP_ALLOW_NO_AUTH = os.getenv("MCP_ALLOW_NO_AUTH", "").lower() in ("1", "true", "yes")
UI_SECRET = os.getenv("UI_SECRET", "") or MCP_SECRET
HA_INGRESS_MODE = os.getenv("HA_INGRESS_MODE", "").lower() in ("1", "true", "yes")

if not HA_URL or not HA_TOKEN:
    raise RuntimeError("HA_URL and HA_TOKEN must be set in .env")

if not MCP_SECRET and not MCP_ALLOW_NO_AUTH:
    raise RuntimeError(
        "MCP_SECRET is not set. Set it to a strong random token (openssl rand -base64 32) "
        "or set MCP_ALLOW_NO_AUTH=true to explicitly run without authentication (trusted networks only)."
    )

HEADERS = {
    "Authorization": f"Bearer {HA_TOKEN}",
    "Content-Type": "application/json",
}

# host, port and the HTTP path moved out of the constructor in MCP SDK 2.0:
# they are arguments of streamable_http_app(), see server.py.
mcp = MCPServer("Home Assistant Advanced")

HELPER_DOMAINS = {
    "input_boolean", "input_number", "input_text",
    "input_select", "input_datetime", "counter", "timer", "input_button",
}


def _slug(name: str) -> str:
    """Convert a human name to a valid HA slug."""
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _parse_remote_prefixes(raw: str) -> dict:
    """Parse a remote-instance list into {group_name: entity_id_prefix}.

    Several Home Assistant instances are often joined by exposing the remote
    entities on a main one, where they show up under a shared entity_id prefix.
    Tools that group by location use this map to report those entities under the
    instance they come from instead of the local area registry.

    Format: a comma-separated list where each item is either "name" — the prefix
    then defaults to "sensor.<name>_" — or "name=prefix" when the entity_id
    prefix does not follow that convention. Example:

        HA_REMOTE_PREFIXES="annex,workshop=sensor.ws_"

    Empty by default: with nothing configured no entity is treated as remote,
    and grouping falls back entirely to the area registry.
    """
    prefixes: dict = {}
    for item in raw.split(","):
        name, sep, prefix = item.partition("=")
        name = name.strip()
        prefix = prefix.strip()
        if not name:
            continue
        prefixes[name] = prefix if sep and prefix else f"sensor.{_slug(name)}_"
    return prefixes


REMOTE_PREFIXES = _parse_remote_prefixes(os.getenv("HA_REMOTE_PREFIXES", ""))

# Substrings that mark a media_player as an Amazon Echo, which is announced to
# through alexa_media rather than the regular TTS service. The two defaults match
# how the Alexa Media Player integration names its entities; add your own when a
# speaker group is named after the room or the household instead.
ALEXA_KEYWORDS = tuple(
    kw.strip().lower()
    for kw in os.getenv("HA_ALEXA_KEYWORDS", "echo,alexa").split(",")
    if kw.strip()
)

_DEFAULT_LANGUAGE = ""


def default_language() -> str:
    """The language configured in Home Assistant, fetched once and cached.

    Used as the default for TTS and conversation tools, so that an instance set
    up in any language behaves correctly without configuring it twice. Falls
    back to English if /api/config cannot be read.
    """
    global _DEFAULT_LANGUAGE
    if not _DEFAULT_LANGUAGE:
        try:
            import httpx
            with httpx.Client() as client:
                r = client.get(f"{HA_URL}/api/config", headers=HEADERS, timeout=10)
                r.raise_for_status()
                _DEFAULT_LANGUAGE = r.json().get("language") or "en"
        except Exception:
            _DEFAULT_LANGUAGE = "en"
    return _DEFAULT_LANGUAGE


def _run_in_new_loop(coro):
    """Run a coroutine in a fresh event loop (safe to call from inside uvicorn)."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _ws(msg: dict) -> dict:
    """Send one WS command over a single authenticated connection (sync, thread-safe)."""
    return _ws_multi([msg])[0]


def _ws_multi(msgs: list) -> list:
    """Send multiple WS commands over a single authenticated connection (sync, thread-safe)."""
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(_run_in_new_loop, _ws_commands(msgs)).result(timeout=30)


async def _ws_commands(msgs: list) -> list:
    """Async: open one WS connection, authenticate, send all msgs, return list of results.

    Sends all commands first, then collects result messages by id — skipping event
    messages and unsolicited frames that HA may send between command results.
    """
    import websockets
    ws_url = HA_URL.replace("https://", "wss://").replace("http://", "ws://") + "/api/websocket"
    async with websockets.connect(ws_url, open_timeout=10, max_size=10 * 1024 * 1024) as ws:
        m = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
        if m.get("type") != "auth_required":
            return [{"error": f"Expected auth_required, got: {m}"}] * len(msgs)
        await ws.send(json.dumps({"type": "auth", "access_token": HA_TOKEN}))
        m = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
        if m.get("type") != "auth_ok":
            return [{"error": f"Auth failed: {m}"}] * len(msgs)

        # Send all commands first
        for i, msg in enumerate(msgs, start=1):
            await ws.send(json.dumps({"id": i, **msg}))

        # Collect result messages by id, skipping event/unsolicited frames
        results: list = [None] * len(msgs)
        pending = set(range(1, len(msgs) + 1))
        while pending:
            m = json.loads(await asyncio.wait_for(ws.recv(), timeout=15))
            if m.get("type") == "result" and m.get("id") in pending:
                results[m["id"] - 1] = m
                pending.discard(m["id"])
        return results
