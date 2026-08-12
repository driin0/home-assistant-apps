import tools._base  # triggers load_dotenv and mcp init
import tools.diagnostics
import tools.automations
import tools.scripts
import tools.scenes
import tools.helpers
import tools.notifications
import tools.cameras
import tools.areas
import tools.lights
import tools.switches
import tools.sensors
import tools.climate
import tools.media_players
import tools.locks
import tools.fans
import tools.covers
import tools.vacuum
import tools.weather
import tools.persons
import tools.alarm
import tools.system
import tools.calendar
import tools.todo
import tools.statistics
import tools.buttons
import tools.addons
import tools.dashboards
import tools.hacs
import tools.assist
import tools.groups
import tools.users
import tools.tags
import tools.alerts
import tools.prompts

if __name__ == "__main__":
    import hmac
    import time
    import threading
    import uvicorn
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.responses import Response as StarletteResponse
    from tools._base import mcp, MCP_PORT, MCP_SECRET
    from web import start as start_web_ui
    import stats

    # Patch tool manager to track call counts, latency and errors
    _orig_call = mcp._tool_manager.call_tool

    async def _tracked_call(name: str, arguments: dict, **kwargs):
        t0 = time.monotonic()
        try:
            result = await _orig_call(name, arguments, **kwargs)
            stats.record_call(name, (time.monotonic() - t0) * 1000)
            return result
        except Exception as e:
            stats.record_call(name, (time.monotonic() - t0) * 1000)
            stats.record_error(name, e)
            raise

    mcp._tool_manager.call_tool = _tracked_call

    threading.Thread(target=start_web_ui, daemon=True, name="web-ui").start()

    app = mcp.streamable_http_app()

    if MCP_SECRET:
        _secret_bytes = MCP_SECRET.encode("utf-8")

        class BearerAuthMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request, call_next):
                header = request.headers.get("Authorization", "")
                token = header[7:] if header.startswith("Bearer ") else ""
                if not hmac.compare_digest(token.encode("utf-8"), _secret_bytes):
                    return StarletteResponse("Unauthorized", status_code=401)
                return await call_next(request)

        app.add_middleware(BearerAuthMiddleware)

    uvicorn.run(
        app,
        host=mcp.settings.host,
        port=mcp.settings.port,
        log_level=mcp.settings.log_level.lower(),
    )
