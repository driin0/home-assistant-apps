#!/usr/bin/with-contenv bashio

PORT=$(bashio::config 'port' '31996')
export PORT="${PORT}"
export DATA_DIR="/config/data"

bashio::log.info "Starting iliad-tools on port ${PORT}..."
exec node /app/server.js
