"""
In-memory call statistics for the MCP server.
Thread-safe — updated from the MCP worker threads, read from the web UI thread.
Stats reset on server restart (session-only).
"""

import threading
from collections import deque
from datetime import datetime, timezone

_lock = threading.Lock()
_call_counts: dict[str, int] = {}
_last_call: dict | None = None
_recent_errors: deque = deque(maxlen=20)


def record_call(tool_name: str, latency_ms: float) -> None:
    global _last_call
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with _lock:
        _call_counts[tool_name] = _call_counts.get(tool_name, 0) + 1
        _last_call = {
            "tool": tool_name,
            "at": now,
            "latency_ms": round(latency_ms, 1),
            "count": _call_counts[tool_name],
        }


def _redact(text: str) -> str:
    """Strip HA_URL and HA_TOKEN from error messages so stack traces don't leak
    internal endpoints or credentials. Imported lazily to avoid circular imports."""
    from tools._base import HA_URL, HA_TOKEN
    if HA_TOKEN:
        text = text.replace(HA_TOKEN, "<redacted>")
    if HA_URL:
        text = text.replace(HA_URL, "<ha>")
    return text


def record_error(tool_name: str, error) -> None:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    msg = _redact(str(error))[:200]
    if not isinstance(error, str):
        msg = f"{type(error).__name__}: {msg}"
    with _lock:
        _recent_errors.append({
            "tool": tool_name,
            "error": msg,
            "at": now,
        })


def get_stats() -> dict:
    with _lock:
        return {
            "call_counts": dict(
                sorted(_call_counts.items(), key=lambda x: -x[1])
            ),
            "total_calls": sum(_call_counts.values()),
            "last_call": dict(_last_call) if _last_call else None,
            "recent_errors": list(_recent_errors),
        }
