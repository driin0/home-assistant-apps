import base64
import hmac
import json
import os
import time
from datetime import datetime, timezone
from html import escape as esc

import httpx
import uvicorn
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, Response as StarletteResponse
from starlette.routing import Route

from tools._base import HA_INGRESS_MODE, HA_URL, HEADERS, MCP_ALLOW_NO_AUTH, MCP_PORT, MCP_SECRET, UI_SECRET, mcp
import stats as _stats

START_TIME = datetime.now(timezone.utc)
UI_PORT = int(os.getenv("UI_PORT", "47822"))

# HA live data cache (30 s TTL) — avoids hammering HA on every page load
_ha_cache: dict = {"data": None, "at": 0.0}
_HA_CACHE_TTL = 30.0


def _ha_fetch() -> dict:
    """Fetch HA config + live state summary. Cached for 30 s."""
    now = time.monotonic()
    if _ha_cache["data"] and now - _ha_cache["at"] < _HA_CACHE_TTL:
        return _ha_cache["data"]
    try:
        with httpx.Client() as client:
            cfg = client.get(f"{HA_URL}/api/config", headers=HEADERS, timeout=5).json()
            t0 = time.monotonic()
            states_r = client.get(f"{HA_URL}/api/states", headers=HEADERS, timeout=10)
            ha_latency_ms = round((time.monotonic() - t0) * 1000, 1)
            states = states_r.json()

        entity_count = len(states)
        lights_on = sum(
            1 for s in states
            if s["entity_id"].startswith("light.") and s["state"] == "on"
        )
        alarm_entities = [
            s for s in states if s["entity_id"].startswith("alarm_control_panel.")
        ]
        alarm_state = alarm_entities[0]["state"] if alarm_entities else None

        result = {
            "ok": True,
            "version": cfg.get("version", ""),
            "location_name": cfg.get("location_name", ""),
            "time_zone": cfg.get("time_zone", ""),
            "entity_count": entity_count,
            "lights_on": lights_on,
            "alarm_state": alarm_state,
            "ha_latency_ms": ha_latency_ms,
        }
    except Exception as e:
        result = {"ok": False, "error": str(e)}

    _ha_cache["data"] = result
    _ha_cache["at"] = time.monotonic()
    return result


def _tool_list() -> list:
    try:
        return [
            {"name": n, "description": (t.description or "").split("\n")[0].strip()}
            for n, t in sorted(mcp._tool_manager._tools.items())
        ]
    except AttributeError:
        return []


def _prompt_list() -> list:
    try:
        return [
            {"name": n, "description": (p.description or "").strip()}
            for n, p in sorted(mcp._prompt_manager._prompts.items())
        ]
    except AttributeError:
        return []


async def status_json(request: Request) -> JSONResponse:
    ha = _ha_fetch()
    s = _stats.get_stats()
    tools = _tool_list()
    prompts = _prompt_list()
    uptime = int((datetime.now(timezone.utc) - START_TIME).total_seconds())
    return JSONResponse({
        "ha": ha,
        "ha_url": HA_URL,
        "tools": tools,
        "tool_count": len(tools),
        "prompts": prompts,
        "prompt_count": len(prompts),
        "mcp_port": MCP_PORT,
        "mcp_auth": bool(MCP_SECRET),
        "uptime_seconds": uptime,
        **s,
    })


def _render_items(items: list) -> str:
    if not items:
        return '<p class="empty">None</p>'
    rows = []
    for item in items:
        name = esc(item["name"])
        desc = esc(item.get("description", ""))
        rows.append(
            f'<div class="item">'
            f'<span class="item-name">{name}</span>'
            f'{"<span class=item-desc>" + desc + "</span>" if desc else ""}'
            f'</div>'
        )
    return "\n".join(rows)


def _render_top_tools(call_counts: dict) -> str:
    if not call_counts:
        return '<p class="empty">No calls yet this session</p>'
    max_count = max(call_counts.values(), default=1)
    rows = []
    for name, count in list(call_counts.items())[:15]:
        pct = round(count / max_count * 100)
        rows.append(
            f'<div class="top-tool">'
            f'<span class="top-tool-name">{esc(name)}</span>'
            f'<div class="top-tool-bar-wrap">'
            f'<div class="top-tool-bar" style="width:{pct}%"></div>'
            f'</div>'
            f'<span class="top-tool-count">{int(count)}</span>'
            f'</div>'
        )
    return "\n".join(rows)


def _render_errors(errors: list) -> str:
    if not errors:
        return '<p class="empty ok-text">No errors this session</p>'
    rows = []
    for e in reversed(errors[-5:]):
        rows.append(
            f'<div class="error-item">'
            f'<span class="error-tool">{esc(e["tool"])}</span>'
            f'<span class="error-at">{esc(e["at"][11:19])}</span>'
            f'<span class="error-msg">{esc(e["error"])}</span>'
            f'</div>'
        )
    return "\n".join(rows)


async def index(request: Request) -> HTMLResponse:
    ingress_path = request.headers.get("X-Ingress-Path", "").rstrip("/")
    api_url_js = json.dumps(f"{ingress_path}/api/status")

    uptime_seconds = int((datetime.now(timezone.utc) - START_TIME).total_seconds())
    h, rem = divmod(uptime_seconds, 3600)
    m, s = divmod(rem, 60)
    uptime_str = f"{h}h {m}m {s}s"
    start_str = START_TIME.strftime("%Y-%m-%d %H:%M UTC")

    ha = _ha_fetch()
    st = _stats.get_stats()
    tools = _tool_list()
    prompts = _prompt_list()

    ha_ok = ha["ok"]
    ha_version = esc(ha.get("version", "") if ha_ok else "")
    ha_location = esc(ha.get("location_name", "") if ha_ok else "")
    ha_tz = esc(ha.get("time_zone", "") if ha_ok else "")
    ha_error = esc(ha.get("error", "") if not ha_ok else "")
    entity_count = ha.get("entity_count", "?") if ha_ok else "?"
    lights_on = ha.get("lights_on", 0) if ha_ok else 0
    alarm_state = ha.get("alarm_state") if ha_ok else None
    ha_latency = ha.get("ha_latency_ms", "?") if ha_ok else "?"
    ha_url_safe = esc(HA_URL)

    auth_ok = bool(MCP_SECRET)
    last_call = st["last_call"]
    total_calls = st["total_calls"]

    alarm_badge = ""
    if alarm_state:
        alarm_cls = "badge-ok" if "armed" in alarm_state else "badge-warn" if alarm_state == "disarmed" else "badge-err"
        alarm_badge = f'<span class="badge {alarm_cls}">{esc(alarm_state)}</span>'

    last_call_tool = esc(last_call["tool"]) if last_call else ""
    last_call_at = esc(last_call["at"][11:19]) if last_call else ""
    last_call_latency = last_call["latency_ms"] if last_call else ""
    last_call_count = last_call["count"] if last_call else ""

    html = f"""<!DOCTYPE html>
<html lang="en" data-theme="auto">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HA Manager{" — " + ha_location if ha_location else ""}</title>
<style>
:root {{
  --bg: #f1f5f9;
  --surface: #ffffff;
  --border: #e2e8f0;
  --text: #0f172a;
  --text-muted: #64748b;
  --accent: #3b82f6;
  --accent-dim: #dbeafe;
  --ok: #16a34a;
  --ok-bg: #dcfce7;
  --warn: #d97706;
  --warn-bg: #fef3c7;
  --err: #dc2626;
  --err-bg: #fee2e2;
  --dot-ok: #22c55e;
  --dot-err: #ef4444;
  --shadow: 0 1px 3px rgba(0,0,0,.07), 0 1px 2px rgba(0,0,0,.05);
  --bar: #3b82f6;
}}
@media (prefers-color-scheme: dark) {{
  html[data-theme="auto"] {{
    --bg: #0f172a; --surface: #1e293b; --border: #334155;
    --text: #f1f5f9; --text-muted: #94a3b8;
    --accent-dim: #1e3a5f;
    --ok-bg: #14532d; --warn-bg: #78350f; --err-bg: #7f1d1d;
    --shadow: 0 1px 3px rgba(0,0,0,.3);
    --bar: #60a5fa;
  }}
}}
html[data-theme="dark"] {{
  --bg: #0f172a; --surface: #1e293b; --border: #334155;
  --text: #f1f5f9; --text-muted: #94a3b8;
  --accent-dim: #1e3a5f;
  --ok-bg: #14532d; --warn-bg: #78350f; --err-bg: #7f1d1d;
  --shadow: 0 1px 3px rgba(0,0,0,.3);
  --bar: #60a5fa;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: var(--bg); color: var(--text);
  min-height: 100vh; padding: 24px 16px;
}}
header {{
  display: flex; align-items: center; justify-content: space-between;
  max-width: 900px; margin: 0 auto 24px;
}}
.header-left {{ display: flex; align-items: center; gap: 10px; }}
.logo {{
  width: 32px; height: 32px; background: var(--accent); border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: .85rem; font-weight: 700; flex-shrink: 0;
}}
.header-title {{ font-size: 1.1rem; font-weight: 700; }}
.header-sub {{ font-size: .8rem; color: var(--text-muted); margin-top: 1px; }}
.controls {{ display: flex; gap: 8px; align-items: center; }}
button {{
  background: var(--surface); border: 1px solid var(--border);
  color: var(--text-muted); padding: 6px 12px; border-radius: 6px;
  cursor: pointer; font-size: .8rem; transition: background .15s, color .15s;
}}
button:hover {{ background: var(--border); color: var(--text); }}
.grid {{
  max-width: 900px; margin: 0 auto;
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px;
}}
@media (max-width: 680px) {{ .grid {{ grid-template-columns: 1fr; }} }}
.col2 {{ grid-column: span 2; }}
.full {{ grid-column: 1 / -1; }}
.card {{
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 12px; padding: 18px; box-shadow: var(--shadow);
}}
.card-title {{
  font-size: .65rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: .1em; color: var(--text-muted); margin-bottom: 14px;
}}
.status-row {{ display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }}
.dot {{ width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }}
.dot-ok  {{ background: var(--dot-ok); }}
.dot-err {{ background: var(--dot-err); }}
.badge {{
  font-size: .72rem; font-weight: 600; padding: 2px 8px;
  border-radius: 20px; display: inline-block;
}}
.badge-ok   {{ background: var(--ok-bg);   color: var(--ok);   }}
.badge-warn {{ background: var(--warn-bg); color: var(--warn); }}
.badge-err  {{ background: var(--err-bg);  color: var(--err);  }}
.field {{
  display: flex; justify-content: space-between; align-items: center;
  padding: 7px 0; border-bottom: 1px solid var(--border); font-size: .85rem;
}}
.field:last-child {{ border-bottom: none; }}
.field-label {{ color: var(--text-muted); }}
.field-value {{ font-weight: 500; text-align: right; max-width: 60%; word-break: break-all; }}
.stat-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 12px; }}
.stat {{
  background: var(--bg); border-radius: 8px; padding: 10px; text-align: center;
}}
.stat-value {{ font-size: 1.5rem; font-weight: 700; color: var(--accent); line-height: 1; }}
.stat-label {{
  font-size: .65rem; color: var(--text-muted); margin-top: 3px;
  text-transform: uppercase; letter-spacing: .07em;
}}
/* Live stats row */
.live-row {{
  display: flex; flex-wrap: wrap; gap: 10px; align-items: center;
}}
.live-pill {{
  background: var(--bg); border-radius: 8px; padding: 8px 14px;
  display: flex; flex-direction: column; align-items: center; min-width: 80px;
}}
.live-pill-value {{ font-size: 1.3rem; font-weight: 700; color: var(--accent); }}
.live-pill-label {{ font-size: .65rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: .07em; margin-top: 2px; }}
/* Last call */
.last-call-tool {{
  font-size: 1rem; font-weight: 700; font-family: ui-monospace, "SF Mono", monospace;
  color: var(--accent); margin-bottom: 10px; word-break: break-all;
}}
.last-call-none {{ color: var(--text-muted); font-size: .875rem; }}
/* Top tools */
.top-tool {{
  display: grid; grid-template-columns: 1fr 3fr auto;
  align-items: center; gap: 8px; margin-bottom: 6px; font-size: .8rem;
}}
.top-tool-name {{
  font-family: ui-monospace, "SF Mono", monospace; font-size: .75rem;
  color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}}
.top-tool-bar-wrap {{ background: var(--bg); border-radius: 4px; height: 6px; overflow: hidden; }}
.top-tool-bar {{ background: var(--bar); height: 6px; border-radius: 4px; transition: width .3s; }}
.top-tool-count {{ color: var(--text-muted); font-size: .75rem; text-align: right; min-width: 24px; }}
/* Errors */
.error-item {{
  display: grid; grid-template-columns: auto auto 1fr;
  gap: 8px; align-items: baseline;
  padding: 7px 0; border-bottom: 1px solid var(--border); font-size: .8rem;
}}
.error-item:last-child {{ border-bottom: none; }}
.error-tool {{ font-family: ui-monospace, monospace; color: var(--err); font-weight: 600; }}
.error-at {{ color: var(--text-muted); font-size: .72rem; white-space: nowrap; }}
.error-msg {{ color: var(--text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
/* Collapsible tool/prompt lists */
details {{ margin-top: 4px; }}
details summary {{
  cursor: pointer; font-size: .72rem; font-weight: 600; color: var(--text-muted);
  text-transform: uppercase; letter-spacing: .07em;
  list-style: none; display: flex; align-items: center; gap: 6px; user-select: none;
}}
details summary::before {{ content: "▶"; font-size: .55rem; transition: transform .15s; }}
details[open] summary::before {{ transform: rotate(90deg); }}
.item-list {{
  margin-top: 10px; display: flex; flex-direction: column; gap: 1px;
  max-height: 300px; overflow-y: auto;
}}
.item {{
  display: flex; flex-direction: column; padding: 6px 10px;
  border-radius: 6px; background: var(--bg);
}}
.item-name {{ font-size: .78rem; font-weight: 600; font-family: ui-monospace, monospace; color: var(--accent); }}
.item-desc {{ font-size: .72rem; color: var(--text-muted); margin-top: 1px; line-height: 1.4; }}
.empty {{ color: var(--text-muted); font-size: .85rem; }}
.ok-text {{ color: var(--ok); }}
footer {{
  max-width: 900px; margin: 16px auto 0;
  text-align: right; font-size: .72rem; color: var(--text-muted);
}}
</style>
</head>
<body>
<header>
  <div class="header-left">
    <span class="logo">HA</span>
    <div>
      <div class="header-title">HA Manager</div>
      {f'<div class="header-sub" id="header-sub">{ha_location}</div>' if ha_location else '<div class="header-sub" id="header-sub"></div>'}
    </div>
  </div>
  <div class="controls">
    <button id="refresh-btn" onclick="refresh()">Refresh</button>
    <button id="theme-btn" onclick="cycleTheme()"></button>
  </div>
</header>

<div class="grid">

  <!-- HA Status -->
  <div class="card">
    <div class="card-title">Home Assistant</div>
    <div class="status-row">
      <span class="dot {'dot-ok' if ha_ok else 'dot-err'}" id="ha-dot"></span>
      <span class="badge {'badge-ok' if ha_ok else 'badge-err'}" id="ha-badge">{'Connected' if ha_ok else 'Unreachable'}</span>
    </div>
    <div class="field"><span class="field-label">URL</span><span class="field-value">{ha_url_safe}</span></div>
    <div class="field"><span class="field-label">Version</span><span class="field-value" id="ha-version">{ha_version}</span></div>
    <div class="field"><span class="field-label">Location</span><span class="field-value" id="ha-location">{ha_location}</span></div>
    <div class="field"><span class="field-label">Timezone</span><span class="field-value" id="ha-tz">{ha_tz}</span></div>
    <div class="field"><span class="field-label">Latency</span><span class="field-value" id="ha-latency">{ha_latency} ms</span></div>
    {'<div class="field"><span class="field-label">Error</span><span class="field-value" style="color:var(--err)">' + ha_error + '</span></div>' if ha_error else ''}
  </div>

  <!-- MCP Server -->
  <div class="card">
    <div class="card-title">MCP Server</div>
    <div class="field"><span class="field-label">Port</span><span class="field-value">{MCP_PORT}</span></div>
    <div class="field">
      <span class="field-label">Auth</span>
      <span class="field-value">
        <span class="badge {'badge-ok' if auth_ok else 'badge-warn'}">{'Protected' if auth_ok else 'No auth'}</span>
      </span>
    </div>
    <div class="field"><span class="field-label">Total calls</span><span class="field-value" id="total-calls">{total_calls}</span></div>
    <div class="stat-grid">
      <div class="stat"><div class="stat-value" id="tool-count">{len(tools)}</div><div class="stat-label">Tools</div></div>
      <div class="stat"><div class="stat-value" id="prompt-count">{len(prompts)}</div><div class="stat-label">Prompts</div></div>
    </div>
  </div>

  <!-- Server -->
  <div class="card">
    <div class="card-title">Server</div>
    <div class="field"><span class="field-label">Started</span><span class="field-value">{start_str}</span></div>
    <div class="field"><span class="field-label">Uptime</span><span class="field-value" id="uptime">{uptime_str}</span></div>
  </div>

  <!-- HA Live -->
  <div class="card full">
    <div class="card-title">Live</div>
    <div class="live-row">
      <div class="live-pill">
        <span class="live-pill-value" id="entity-count">{entity_count}</span>
        <span class="live-pill-label">Entities</span>
      </div>
      <div class="live-pill">
        <span class="live-pill-value" id="lights-on">{lights_on}</span>
        <span class="live-pill-label">Lights on</span>
      </div>
      {'<div class="live-pill"><span class="live-pill-label" style="margin-bottom:4px">Alarm</span>' + alarm_badge + '</div>' if alarm_state else ''}
    </div>
  </div>

  <!-- Last Activity -->
  <div class="card col2">
    <div class="card-title">Last Activity</div>
    {'<div class="last-call-tool" id="last-call-tool">' + last_call_tool + '</div>' if last_call else '<div class="last-call-none" id="last-call-tool">No calls yet this session</div>'}
    {f'''<div class="field"><span class="field-label">Time</span><span class="field-value" id="last-call-at">{last_call_at} UTC</span></div>
    <div class="field"><span class="field-label">Latency</span><span class="field-value" id="last-call-latency">{last_call_latency} ms</span></div>
    <div class="field"><span class="field-label">Calls to this tool</span><span class="field-value" id="last-call-count">{last_call_count}</span></div>''' if last_call else ''}
  </div>

  <!-- Errors -->
  <div class="card">
    <div class="card-title">Recent Errors</div>
    <div id="error-list">{_render_errors(st["recent_errors"])}</div>
  </div>

  <!-- Top Tools -->
  <div class="card full">
    <div class="card-title">Top Tools (this session)</div>
    <div id="top-tools">{_render_top_tools(st["call_counts"])}</div>
  </div>

  <!-- Tool & Prompt lists -->
  <div class="card full">
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:24px">
      <div>
        <div class="card-title">Tools ({len(tools)})</div>
        <details>
          <summary>Show all</summary>
          <div class="item-list" id="tool-list">{_render_items(tools)}</div>
        </details>
      </div>
      <div>
        <div class="card-title">Prompts ({len(prompts)})</div>
        <details>
          <summary>Show all</summary>
          <div class="item-list" id="prompt-list">{_render_items(prompts)}</div>
        </details>
      </div>
    </div>
  </div>

</div>

<footer><span id="last-updated">Loaded {datetime.now().strftime("%H:%M:%S")}</span></footer>

<script>
const API = {api_url_js};
const THEMES = ["auto","light","dark"], ICONS = ["◐","☀","☾"];

function applyTheme(t) {{
  document.documentElement.setAttribute("data-theme", t);
  document.getElementById("theme-btn").textContent = ICONS[THEMES.indexOf(t)];
}}
function cycleTheme() {{
  const cur = document.documentElement.getAttribute("data-theme") || "auto";
  const next = THEMES[(THEMES.indexOf(cur)+1) % THEMES.length];
  localStorage.setItem("ha-manager-theme", next);
  applyTheme(next);
}}
function fmtUptime(s) {{
  const h = Math.floor(s/3600), r = s%3600, m = Math.floor(r/60), sec = r%60;
  return h+"h "+m+"m "+sec+"s";
}}
function set(id, val) {{ const el = document.getElementById(id); if (el) el.textContent = val; }}
function escapeHtml(s) {{
  return String(s ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}}

function renderItems(items) {{
  if (!items.length) return '<p class="empty">None</p>';
  return items.map(i =>
    `<div class="item"><span class="item-name">${{escapeHtml(i.name)}}</span>${{i.description ? `<span class="item-desc">${{escapeHtml(i.description)}}</span>` : ""}}</div>`
  ).join("");
}}

function renderTopTools(counts) {{
  const entries = Object.entries(counts);
  if (!entries.length) return '<p class="empty">No calls yet this session</p>';
  const max = Math.max(...entries.map(e => e[1]));
  return entries.slice(0,15).map(([name, count]) =>
    `<div class="top-tool">
      <span class="top-tool-name">${{escapeHtml(name)}}</span>
      <div class="top-tool-bar-wrap"><div class="top-tool-bar" style="width:${{Math.round(count/max*100)}}%"></div></div>
      <span class="top-tool-count">${{Number(count) | 0}}</span>
    </div>`
  ).join("");
}}

function renderErrors(errors) {{
  if (!errors.length) return '<p class="empty ok-text">No errors this session</p>';
  return [...errors].reverse().slice(0,5).map(e =>
    `<div class="error-item">
      <span class="error-tool">${{escapeHtml(e.tool)}}</span>
      <span class="error-at">${{escapeHtml(String(e.at).substring(11,19))}}</span>
      <span class="error-msg">${{escapeHtml(e.error)}}</span>
    </div>`
  ).join("");
}}

async function refresh() {{
  const btn = document.getElementById("refresh-btn");
  btn.textContent = "..."; btn.disabled = true;
  try {{
    const d = await (await fetch(API)).json();

    // HA status
    const ok = d.ha.ok;
    document.getElementById("ha-dot").className   = "dot " + (ok ? "dot-ok" : "dot-err");
    document.getElementById("ha-badge").textContent  = ok ? "Connected" : "Unreachable";
    document.getElementById("ha-badge").className    = "badge " + (ok ? "badge-ok" : "badge-err");
    set("ha-version",  d.ha.version       || "");
    set("ha-location", d.ha.location_name || "");
    set("ha-tz",       d.ha.time_zone     || "");
    set("ha-latency",  (d.ha.ha_latency_ms ?? "?") + " ms");
    set("header-sub",  d.ha.location_name || "");
    set("entity-count", d.ha.entity_count ?? "?");
    set("lights-on",    d.ha.lights_on    ?? 0);

    // MCP
    set("tool-count",   d.tool_count);
    set("prompt-count", d.prompt_count);
    set("total-calls",  d.total_calls);
    set("uptime",       fmtUptime(d.uptime_seconds));

    // Last call
    const lc = d.last_call;
    const lcEl = document.getElementById("last-call-tool");
    if (lcEl) {{
      lcEl.textContent = lc ? lc.tool : "No calls yet this session";
      lcEl.className   = lc ? "last-call-tool" : "last-call-none";
    }}
    set("last-call-at",      lc ? lc.at.substring(11,19) + " UTC" : "");
    set("last-call-latency", lc ? lc.latency_ms + " ms"           : "");
    set("last-call-count",   lc ? lc.count                        : "");

    // Dynamic sections
    document.getElementById("top-tools").innerHTML   = renderTopTools(d.call_counts || {{}});
    document.getElementById("error-list").innerHTML  = renderErrors(d.recent_errors || []);
    document.getElementById("tool-list").innerHTML   = renderItems(d.tools   || []);
    document.getElementById("prompt-list").innerHTML = renderItems(d.prompts || []);

    document.getElementById("last-updated").textContent = "Updated " + new Date().toLocaleTimeString();
  }} catch(e) {{
    document.getElementById("last-updated").textContent = "Refresh failed: " + e;
  }} finally {{
    btn.textContent = "Refresh"; btn.disabled = false;
  }}
}}

applyTheme(localStorage.getItem("ha-manager-theme") || "auto");
setInterval(refresh, 30000);
</script>
</body>
</html>"""
    return HTMLResponse(html)


class BasicAuthMiddleware(BaseHTTPMiddleware):
    """Protect the status UI with HTTP Basic Auth. Username is ignored; the
    password must match UI_SECRET in constant time."""

    def __init__(self, app, secret: str):
        super().__init__(app)
        self._secret = secret.encode("utf-8")

    async def dispatch(self, request, call_next):
        header = request.headers.get("Authorization", "")
        if header.startswith("Basic "):
            try:
                decoded = base64.b64decode(header[6:], validate=True).decode("utf-8", "replace")
                _, _, pwd = decoded.partition(":")
                if hmac.compare_digest(pwd.encode("utf-8"), self._secret):
                    return await call_next(request)
            except (ValueError, UnicodeDecodeError):
                pass
        return StarletteResponse(
            "Unauthorized",
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="HA Manager"'},
        )


app = Starlette(routes=[
    Route("/", index),
    Route("/api/status", status_json),
])

if HA_INGRESS_MODE:
    # UI is reached only via the HA Supervisor Ingress proxy, which authenticates
    # the user upstream. Do not apply Basic Auth (Ingress requests have no
    # Authorization header and would be 401'd).
    pass
elif UI_SECRET:
    app.add_middleware(BasicAuthMiddleware, secret=UI_SECRET)
elif not MCP_ALLOW_NO_AUTH:
    raise RuntimeError(
        "UI_SECRET is not set and MCP_SECRET is empty. Set UI_SECRET (or MCP_SECRET) "
        "to a strong random token, set HA_INGRESS_MODE=true when running behind HA "
        "Ingress, or set MCP_ALLOW_NO_AUTH=true to expose the status UI without "
        "authentication (trusted networks only)."
    )


def start() -> None:
    uvicorn.run(app, host="0.0.0.0", port=UI_PORT, log_level="warning")
