# HA MCP Server

Custom MCP (Model Context Protocol) server that exposes Home Assistant's REST and WebSocket APIs as tools for Claude Code.

## Configuration

### `mcp_port` (default: `47821`)

TCP port the MCP HTTP server listens on. Change only if 47821 conflicts with another service.

### `mcp_secret` (required)

Bearer token to protect the MCP endpoint. The add-on refuses to start if this is not set (unless `mcp_allow_no_auth` is explicitly enabled).

Generate a secure token:

```bash
openssl rand -base64 32
```

### `mcp_allow_no_auth` (default: `false`)

Set to `true` to run without authentication. Only acceptable on fully trusted local networks where the MCP port is not reachable from the internet. When this is `true`, `mcp_secret` is not required.

## Claude Code setup

Add to your `.mcp.json`:

```json
{
  "mcpServers": {
    "homeassistant": {
      "type": "http",
      "url": "http://YOUR_HA_HOST:47821/",
      "headers": {
        "Authorization": "Bearer YOUR_MCP_SECRET"
      }
    }
  }
}
```

Replace `YOUR_HA_HOST` with the IP or hostname of your Home Assistant instance.

Omit `headers` only if `mcp_allow_no_auth: true` is set (trusted local network only).

## Status dashboard

The add-on includes a built-in web UI available directly in the Home Assistant sidebar — no reverse proxy or extra port needed.

Click **HA MCP Server** in the sidebar (or open it from the add-on page via **Open Web UI**) to access the dashboard.

### What the dashboard shows

| Card | Content |
|------|---------|
| **HA Status** | Connection state, HA version, location, timezone |
| **MCP Server** | Tool count, prompt count, MCP port |
| **Server** | Add-on version, uptime |
| **Live** | Total entities, lights currently on, alarm state |
| **Last Activity** | Most recently called tool, timestamp, latency |
| **Recent Errors** | Last 20 tool errors (tool name, message, time) |
| **Top Tools** | Bar chart of the most called tools this session |
| **Tools** | Full list of all registered tools with descriptions (collapsible) |
| **Prompts** | Full list of all registered prompts with descriptions (collapsible) |

All cards refresh automatically every 30 seconds. Stats (call counts, errors, last activity) reset when the add-on restarts.

### Ports

| Port | Purpose |
|------|---------|
| `47821` | MCP HTTP server — used by Claude Code |
| `47822` | Status web UI — served via HA ingress (sidebar) |

The web UI port is internal only and never needs to be opened through your firewall or reverse proxy. The MCP port is the only one that should be exposed externally.

## Proxy-only mode (recommended when a reverse proxy runs on the same host)

If you reach the MCP endpoint exclusively through a reverse proxy (Zoraxy, NGINX Proxy Manager, etc.) that also runs as a Home Assistant add-on, you can **hide the MCP port from the LAN** entirely — only the proxy will be able to reach it.

1. Open the add-on **Configuration → Network** page.
2. Clear the host port next to `47821/tcp` (leave the field empty) and save.
3. Restart the add-on.

The MCP endpoint will no longer be published on the host interface. Other add-ons on the `hassio` Docker network keep full access through the Supervisor-generated hostname:

```
http://25373aee-ha-mcp-server:47821
```

That prefix is not random and not specific to your machine: the Supervisor derives it from the repository URL, as the first eight characters of its SHA1. Everyone who adds this repository as `https://github.com/driin0/home-assistant-apps` therefore gets the same hostname.

It does depend on the exact string you added, though — a trailing slash or a `.git` suffix produces a different prefix. If the name above does not resolve, read the real one from the add-on startup log or the add-on **Info** page.

Point your reverse proxy at that URL. Clients outside HA still reach the MCP through the proxy's public hostname over HTTPS, while the raw `47821/tcp` endpoint is no longer reachable from the LAN.

## Notes

- No token configuration needed — the add-on uses the Supervisor token automatically.
- The server accesses HA internally via the Supervisor proxy (`http://supervisor/core`), so REST and WebSocket both work without a long-lived access token.
- The MCP endpoint is served at `/` — compatible with reverse proxies that strip the path prefix.
