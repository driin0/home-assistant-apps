# Changelog

## 0.0.66 — 2026-08-12

- New option: `remote_prefixes` — the entity_id prefixes of remote instances are now configuration rather than built-in. `get_energy_summary` groups by them when set, and falls back entirely to the area registry when empty, which is the default
- New option: `alexa_keywords` (default `echo,alexa`) — the substrings that mark a media player as an Amazon Echo are now configurable, for speaker groups named after a room rather than after Alexa
- Change: `send_tts`, `broadcast_tts`, `process_conversation` and `create_assist_pipeline` now default `language` to the one configured in Home Assistant (read once from `/api/config`, falling back to English) instead of a fixed value. Pass `language` explicitly to override

## 0.0.65 — 2026-05-29

- Fix: `create_helper` and `delete_helper` now use the WebSocket storage-collection API (`{domain}/create` / `{domain}/delete`) instead of a non-existent REST config endpoint that always returned 404. Helpers are now created exactly like the GUI editor (and show up in Settings → Devices & Services → Helpers)

## 0.0.64 — 2026-04-18

- Fix: remove the unsupported `hostname:` field from `config.yaml` — Home Assistant Supervisor generates hostnames as `<installation-slug>-<addon-name>` and does not honour custom hostnames. The correct DNS name is shown in the add-on startup log and on the Info page
- Docs: proxy-only mode now documents the real Supervisor-generated hostname pattern instead of the custom name that never applied

## 0.0.63 — 2026-04-18

- Attempted (but ineffective): set `hostname: ha-mcp-server` in `config.yaml`. Superseded by 0.0.64
- Docs: first version of the proxy-only mode section (superseded by 0.0.64 with the correct hostname)

## 0.0.62 — 2026-04-17

- Security: MCP bearer check now uses `hmac.compare_digest` (timing-safe) and rejects malformed `Authorization` headers
- Security: HTML-escape all user-visible fields in the status UI (server-side and client-side) to prevent stored XSS via tool names, error messages, and HA config values
- Security: error messages in the Recent Errors panel now redact `HA_URL` and `HA_TOKEN` and include the exception type
- Security: UI auth is skipped when `HA_INGRESS_MODE=true` (set by `run.sh`) — Ingress authentication upstream remains the sole UI gate
- No breaking changes for users; the MCP endpoint still requires a bearer token unless `mcp_allow_no_auth: true`

## 0.0.61 — 2026-04-13

- New: `stats.py` — in-memory session call tracking (counts, latency, errors)
- New: tool manager patched at startup to record every call transparently
- New status page sections: Live HA stats (entities, lights on, alarm), Last Activity (tool + latency + count), Recent Errors, Top Tools bar chart
- Enhancement: instance name shown in page header and title
- Enhancement: HA latency shown in status card, auto-refresh every 30 s

## 0.0.60 — 2026-04-13

- Enhancement: status page shows full tool and prompt lists with names and descriptions (collapsible)
- Tool and prompt lists update on every refresh

## 0.0.59 — 2026-04-13

- Fix: sidebar icon changed to `mdi:robot-happy`

## 0.0.58 — 2026-04-13

- Fix: sidebar icon now uses `panel_icon: mdi:home-assistant` (PNG is only for the addon store card)

## 0.0.57 — 2026-04-13

- Fix: regenerate icon.png at 192x192 (was 128x128) — sidebar now shows correct icon

## 0.0.56 — 2026-04-13

- Fix: status page refresh now updates all fields (dot, version, location, timezone) every 60s

## 0.0.55 — 2026-04-13

- New: status web UI accessible via the HA portal (ingress on port 47822)
- Shows HA connection status, version, location, MCP tool/prompt count, auth status, uptime
- Theme toggle: light / dark / auto (persisted in localStorage)
- Auto-refreshes every 60 seconds via `/api/status` JSON endpoint

## 0.0.54 — 2026-04-12

- Fix: `create_user`, `update_user`, `delete_user` — corrected WS commands to `config/auth/create`, `config/auth/update`, `config/auth/delete` (matching HA frontend)

## 0.0.52 — 2026-04-12

- Fix: `list_users` — correct WS command is `config/auth/list` (not `auth/list_users` which doesn't exist in HA)

## 0.0.51 — 2026-04-12

- Debug: `list_users` — expose HTTP status code from REST fallback to diagnose failures

## 0.0.50 — 2026-04-12

- Debug: `list_users` — log raw WS response when `success: false` to diagnose wrong command name

## 0.0.49 — 2026-04-12

- Fix: `get_system_health` — WS `system_health/info` returns null via Supervisor proxy; fallback to basic HA config info with explanatory note

## 0.0.48 — 2026-04-12

- Fix: code fixes from v0.0.47 were missing from the add-on bundle (only changelog/version were updated)

## 0.0.47 — 2026-04-12

- Fix: WS client now sends all commands first then collects results by id, skipping event/unsolicited frames
- Fix: `list_config_flows` — tries WS `config_entries/flow/progress` first, REST fallback, returns `[]` if both unavailable
- Debug: `get_system_health` — returns raw WS response if result is unexpectedly empty

## 0.0.46 — 2026-04-12

- Fix: `list_users` — added REST fallback to `/api/auth/users` when WS `auth/list_users` returns `unknown_command`
- Fix: `list_config_flows` / `dismiss_config_flow` — switched from WS (unsupported) to REST `/api/config/config_entries/flow`
- Fix: `get_system_health` — switched from REST (404 via Supervisor proxy) to WS `system_health/info`

## 0.0.45 — 2026-04-12

- New tools: `list_users`, `create_user`, `update_user`, `delete_user` — HA user account management
- New tools: `list_tags`, `create_tag`, `update_tag`, `delete_tag` — NFC tag management
- New tools: `list_alerts`, `acknowledge_alert`, `toggle_alert` — alert entity management
- New tools: `list_config_flows`, `dismiss_config_flow` — pending integration flow management
- New tool: `browse_media` — browse media library of any media player
- New tools: `list_device_triggers`, `list_device_conditions`, `list_device_actions` — device automation helpers
- New tool: `get_statistics_summary` — aggregated min/mean/max/delta for multiple entities over N days
- Enhancement: `list_lights` — added `search` and `state` filter parameters

## 0.0.44 — 2026-04-12

- New tools: `create_person`, `update_person`, `delete_person` — full person CRUD (existing list_persons unchanged)
- New tools: `list_lovelace_resources`, `add_lovelace_resource`, `remove_lovelace_resource` — Lovelace frontend resource management
- New tools: `list_assist_pipelines`, `create_assist_pipeline`, `update_assist_pipeline`, `delete_assist_pipeline`, `set_preferred_assist_pipeline` — Assist voice pipeline management
- New tools: `list_groups`, `create_group`, `update_group`, `delete_group` — logical entity group (group.*) management

## 0.0.43 — 2026-04-12

- New tools: `hacs_info`, `list_hacs_repos`, `search_hacs`, `get_hacs_repo`, `install_hacs_repo`, `remove_hacs_repo`, `add_hacs_custom_repo` — HACS management via WebSocket API
- New tools: `get_supervisor_info`, `call_addon_api` — Supervisor info and generic add-on API proxy
- New tool: `set_entity_area` — assign/remove an entity from an area
- New tool: `search_entities` — cross-domain entity search by name, domain, area, label, or state
- New tool: `get_system_health` — HA system health report for all integrations

## 0.0.42 — 2026-04-12

- New tools: `list_addons`, `get_addon`, `start_addon`, `stop_addon`, `restart_addon`, `get_addon_logs` — add-on management via Supervisor API (HA OS / Supervised only)
- New tools: `list_dashboards`, `get_dashboard`, `create_dashboard`, `update_dashboard`, `update_dashboard_config`, `delete_dashboard` — full Lovelace dashboard CRUD
- New tool: `get_entity_dependencies` — find all automations and scripts that reference a given entity (parallel search)
- New tool: `get_entity_exposure` — list entities exposed to voice assistants (Assist, Alexa, Google)
- New tool: `import_blueprint` — import a blueprint from a URL (GitHub, HA Community, etc.)
- New MCP Prompts: `automation_health_audit`, `energy_analysis`, `naming_convention_audit`, `security_overview`, `routine_optimizer` — guided conversation workflows

## 0.0.41 — 2026-04-12

- Enhancement: `list_entities_by_integration` — added `search` (substring filter) and `limit` parameters

## 0.0.40 — 2026-04-12

- Fix: get_live_context remote_instances — connection status only, no power aggregation

## 0.0.39 — 2026-04-12

- Enhancement: `get_live_context` — added `remote_instances` section summarising the state of each connected remote instance

## 0.0.38 — 2026-04-12

- New tool: `bulk_set_entity_labels` — assign labels to multiple entities at once via WS batch
- New tool: `get_energy_summary` — power consumption grouped by area and remote instance

## 0.0.37 — 2026-04-12

- Fix: increase WebSocket max_size to 10MB to support large entity registries
- Fix: `list_entities_by_integration` — restored WS registry approach now that frame size limit is raised

## 0.0.36 — 2026-04-12

- Fix: `list_entities_by_integration` — switch from WS entity registry (too large) to template engine with `integration_entities()`

## 0.0.35 — 2026-04-12

- New tool: `list_entities_by_integration` — list all entities belonging to a specific integration (platform), e.g. `remote_homeassistant`, `shelly`, `yeelight`

## 0.0.34 — 2026-04-12

- New tool: `search_and_play_media` — search and play media on a compatible media player (Spotify, YouTube Music, etc.)
- New tool: `broadcast_tts` — send a TTS announcement to all active media players simultaneously
- New tool: `get_live_context` — concise snapshot of HA state (persons, lights on, alarm, active media, open covers, climate, alerts)

## 0.0.33 — 2026-04-12

- Fix: replace `sleep infinity` with hourly log loop on config error — periodically reminds the user in the logs

## 0.0.32 — 2026-04-12

- Fix: replace `exit 1` with `sleep infinity` on config error to prevent HA restart loop

## 0.0.31 — 2026-04-12

- Security: `mcp_secret` is now required at startup — the add-on refuses to start if not set
- New option: `mcp_allow_no_auth` (default: false) — set to true to explicitly run without authentication (trusted networks only)

## 0.0.30 — 2026-04-11

- New tool: `get_script` — reads the full configuration of a script through the HA config API
- Enhancement: `get_automation` — resolves the numeric id from the entity attributes before calling the config API (avoids the slug→id double attempt)
- Enhancement: `list_notify_services` — added a `type` field (`telegram_private`, `telegram_group`, `other`)

## 0.0.29 — 2026-04-11

- Removed: `search_config` and the YAML fallback in `get_automation` (every GUI automation is reachable through the API by numeric id)
- Removed: the `config:ro` mount from the add-on, the `HA_CONFIG_PATH` variable and the `pyyaml` dependency

## 0.0.28 — 2026-04-11

- Removed: the `config:ro` mount from the add-on (filesystem features remain available in the standalone build through `HA_CONFIG_PATH`)

## 0.0.27 — 2026-04-11

- Fix: `get_automation` — resolves the numeric id from the entity attributes as a second attempt, before the YAML fallback

## 0.0.26 — 2026-04-11

- New tool: `search_config` — full-text search across every YAML file in the HA config

## 0.0.25 — 2026-04-11

- Add-on: added a `config:ro` mount for filesystem access to the HA config

## 0.0.24 — 2026-04-11

- Enhancement: `get_automation` — falls back to reading the YAML files directly (`automations.yaml`, `packages/`) when the config API returns 404
- Added: the `HA_CONFIG_PATH` variable (default `/config`) and the `pyyaml` dependency

## 0.0.23 — 2026-04-11

- New tool: `add_calendar_event` — creates events on any HA calendar entity (timed or all-day)
- New tool: `vacuum_room` — cleans specific segments with a Dreame vacuum (dreame_vacuum.vacuum_clean_segment)
- Fix: `vacuum_control clean_rooms` — corrected the service name to `dreame_vacuum.vacuum_clean_segment`

## 0.0.22 — 2026-04-11

- Fix: `get_weather` — uses WS `call_service` with `return_response: true` for `weather.get_forecasts` (HA 2024.3+); the old REST method returned no forecast data

## 0.0.21 — 2026-04-11

- New tool: `get_energy` — current consumption in watts for every power sensor, highest first
- New tool: `send_tts` — TTS on media players: automatic Alexa announce for Echo devices, tts.speak for the rest
- New tool: `get_entity_registry` — complete registry information for an entity (area, device, disabled_by, labels, and so on)
- Enhancement: `list_automations` — added a `search` parameter to filter by name

## 0.0.20 — 2026-04-11

- Fix: `alarm_control` — corrected the `alarm_` prefix in the HA service names (alarm_arm_home, alarm_disarm, and so on)

## 0.0.19 — 2026-04-11

- New tool: `get_sun` — sun position, sunrise/sunset, dawn/dusk
- New tool: `process_conversation` — sends a text command to the HA conversation agent
- New tool: `trigger_webhook` — triggers an HA webhook by ID
- New tool: `reload_integration` — reloads a config entry without restarting HA
- New tool: `apply_update` — installs a pending update (core, add-on, HACS, firmware)

## 0.0.18 — 2026-04-11

- New tool: `alarm_control` — arms and disarms alarm panels (disarm, arm_home, arm_away, arm_night, arm_vacation)
- New tool: `render_template` — evaluates a Jinja2 template through the HA engine
- New tool: `fire_event` — fires custom events on the HA event bus
- New tool: `create_persistent_notification` — creates persistent notifications in the HA UI
- New tool: `list_zones` — lists HA zones with GPS coordinates and radius
- New tool: `disable_entity` / `enable_entity` — enables and disables entities from the registry
- New tool: `list_backups` / `create_backup` — HA backup management

## 0.0.17 — 2026-04-11

- Fix: `list_repairs` — uses the WebSocket `repairs/list_issues` instead of the REST API (not available through the Supervisor proxy)

## 0.0.16 — 2026-04-11

- Fix: `list_repairs` — handles the 404 gracefully when the Repairs API is not available through the Supervisor proxy

## 0.0.15 — 2026-04-11

- Refactor: server.py split into 26 modules under `tools/` — the main file goes from 2650 to 50 lines

## 0.0.14 — 2026-04-11

- Fix: `set_light` — added the `effect` parameter for light effects (Night, Day, Candle, Twinkle, and so on)

## 0.0.13 — 2026-04-11

- New tools: `list_lights`, `set_light` — light control with brightness, colour temperature, RGB and transition
- New tools: `list_switches`, `toggle_entity` — switches and any toggleable entity
- New tool: `list_sensors` — sensors and binary sensors, filterable by name
- New tool: `press_button` — button and input_button entities
- New tools: `set_number`, `set_select`, `set_text` — the specific input helpers
- New tools: `timer_control`, `counter_control` — timers and counters
- New tool: `get_statistics` — aggregated historical statistics (energy, temperature, and so on)
- New tool: `get_automation_trace` — debugging of automation runs
- New tools: `list_blueprints`, `create_automation_from_blueprint` — automations from blueprints
- New tool: `list_repairs` — pending issues and repairs in HA

## 0.0.12 — 2026-04-11

- Fix: `get_todo_items` — uses WS `call_service` with `return_response: true` to read the items correctly

## 0.0.11 — 2026-04-11

- Fix: `get_todo_items` — uses `todo/get_items` with `return_response` instead of the wrong WS command

## 0.0.10 — 2026-04-11

- Fix: `send_camera_snapshot` — uses the camera access_token to build a public URL reachable from Telegram (instead of the unsupported `file` parameter)

## 0.0.9 — 2026-04-11

- New tool: `send_camera_snapshot` — sends a camera snapshot over Telegram (works around the non-public URL problem by using a local file under `/media`)

## 0.0.8 — 2026-04-11

- Fix: `delete_automation` returns a readable error instead of a 404 for YAML automations
- Fix: `list_schedules` handles the absence of the Scheduler integration correctly
- Fix: `get_weather` uses `weather.get_forecasts` (HA 2024.3+) with a fallback to the legacy attribute
- Fix: `get_camera_snapshot` downloads the image and returns it as base64 (replaces `get_camera_snapshot_url`)

## 0.0.7 — 2026-04-11

- New tools: `list_covers`, `cover_control` — curtains, blinds, garage doors
- New tools: `list_locks`, `lock_control` — locks
- New tools: `list_fans`, `fan_control` — fans
- New tools: `get_weather` — current weather and forecast
- New tools: `list_persons` — people with state and GPS
- New tools: `list_cameras`, `get_camera_snapshot` — cameras with base64 snapshots
- New tools: `list_persistent_notifications`, `dismiss_persistent_notification`
- New tools: `restart_homeassistant`, `list_config_entries`
- New tools: `list_calendars`, `get_calendar_events`
- New tools: `list_todo_lists`, `get_todo_items`, `add_todo_item`, `update_todo_item`, `remove_todo_item`
- Fix: `get_automation` returns a readable error for YAML automations

## 0.0.6 — 2026-04-11

- Fix: `send_photo` — resolves `chat_id` through the entity registry WS (`unique_id`) with a fallback to `friendly_name`

## 0.0.5 — 2026-04-11

- New tools: `send_photo`, `send_notification_with_buttons` (Telegram inline keyboard)
- New tools: `get_automation`, `list_schedules`
- New tools: `get_vacuum_state`, `vacuum_control`
- New tools: `list_climate`, `set_climate`
- New tools: `list_media_players`, `media_player_control`
- New tools: `list_updates`, `get_alarm_state`
- Fix: `list_notify_services` — uses `/api/states` for `notify.*` entities (HA 2024.8+)
- Fix: `send_notification` — migrated to `notify/send_message` with `entity_id` (HA 2024.8+)
- Fix: `list_areas` includes the floor name and floor_id
- Fix: `list_scenes` includes the associated entities
- Fix: corrected the placement of the HA logo in the SVG icon

## 0.0.4 — 2026-04-11

- New tools: `list_areas` with associated entities through the template API, `create_area`, `update_area`, `delete_area`
- New tools: `list_devices`, `get_device`
- New tools: `rename_entity`
- New tools: `list_labels`, `create_label`, `update_label`, `delete_label`, `get_entity_labels`, `set_entity_labels`
- New tools: `list_floors`, `create_floor`, `delete_floor`, `set_area_floor`
- WebSocket batching through `_ws_multi` for registry operations

## 0.0.3 — 2026-04-11

- The server now serves on `/` instead of `/mcp` — compatible with a reverse proxy without path rewriting

## 0.0.2 — 2026-04-11

- Fix: uses `http://supervisor/core` as the internal HA URL — `SUPERVISOR_TOKEN` authenticates through the Supervisor proxy

## 0.0.1 — 2026-04-11

- Initial release
- Tools: automations, scripts, scenes, helpers (all types), template sensors
- Tools: notifications, generic HA service call
- Optional Bearer token auth (`mcp_secret`)
