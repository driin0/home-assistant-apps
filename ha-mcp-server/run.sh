#!/usr/bin/with-contenv bashio

MCP_PORT=$(bashio::config 'mcp_port' '47821')
MCP_SECRET=$(bashio::config 'mcp_secret' '')
MCP_ALLOW_NO_AUTH=$(bashio::config 'mcp_allow_no_auth' 'false')
REMOTE_PREFIXES=$(bashio::config 'remote_prefixes' '')
ALEXA_KEYWORDS=$(bashio::config 'alexa_keywords' 'echo,alexa')

if [ -z "${MCP_SECRET}" ] && [ "${MCP_ALLOW_NO_AUTH}" != "true" ]; then
    while true; do
        bashio::log.fatal "mcp_secret is not set. Configure a strong secret token (openssl rand -base64 32) or enable mcp_allow_no_auth for trusted networks only."
        sleep 3600
    done
fi

# SUPERVISOR_TOKEN authenticates via the Supervisor proxy (not homeassistant:8123 directly)
export HA_URL="http://supervisor/core"
export HA_TOKEN="${SUPERVISOR_TOKEN}"
export MCP_PORT="${MCP_PORT}"
export MCP_SECRET="${MCP_SECRET}"
export MCP_ALLOW_NO_AUTH="${MCP_ALLOW_NO_AUTH}"
export HA_REMOTE_PREFIXES="${REMOTE_PREFIXES}"
export HA_ALEXA_KEYWORDS="${ALEXA_KEYWORDS}"
export UI_PORT="47822"
# Status UI is exposed only via HA Supervisor Ingress — authentication is handled
# upstream by HA. Skip the Basic Auth middleware (Ingress requests carry no
# Authorization header).
export HA_INGRESS_MODE="true"

bashio::log.info "Starting HA MCP Server on port ${MCP_PORT}..."
exec python3 /app/server.py
