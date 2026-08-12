# HA MCP Server – Home Assistant Add-on

![Supports aarch64](https://img.shields.io/badge/aarch64-supported-success)
![Supports amd64](https://img.shields.io/badge/amd64-supported-success)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-Add--on-blue)
![Maintained](https://img.shields.io/badge/Maintained-Yes-brightgreen)

---

## About

Custom MCP (Model Context Protocol) server that exposes Home Assistant's REST and WebSocket APIs as tools for Claude Code.

Provides full access to your HA instance — well beyond what the native HA MCP server offers:

- Full device control: lights, switches, climate, covers, fans, locks, media players, vacuum, alarm, cameras
- Automations, scripts, scenes, helpers, template sensors, groups, blueprints
- Area, floor, label, device and entity registry management
- Calendar, to-do lists, schedules
- Dashboards and Lovelace resources
- Add-on management, HACS, system health, updates and backups
- Assist pipelines, notifications (push, TTS, photo), alerts
- Diagnostics, history, logbook, statistics, energy data

The add-on uses the Supervisor token automatically — no manual token configuration needed.

---

## Installation

1. Go to **Settings → Add-ons → Add-on Store**
2. Click **⋮ → Repositories**
3. Add the repository URL:
   ```
   https://github.com/driin0/home-assistant-apps
   ```
4. Install **HA MCP Server**
5. Configure options (see below)
6. Start the add-on

---

## Configuration

### `mcp_port` (default: `47821`)

TCP port the MCP HTTP server listens on. Change only if 47821 conflicts with another service.

### `mcp_secret` (required)

Bearer token to protect the MCP endpoint. The add-on refuses to start unless this is set or `mcp_allow_no_auth` is explicitly enabled.

Generate a secure token:

```bash
openssl rand -base64 32
```

### `mcp_allow_no_auth` (default: `false`)

Set to `true` to run without authentication. Only acceptable on fully trusted local networks where the MCP port is not reachable from the internet.

### `remote_prefixes` (default: empty)

Optional, and only useful if you run more than one Home Assistant instance. When
a second instance is joined to this one — for example through the
`remote_homeassistant` integration — its entities appear here under a shared
`entity_id` prefix. Listing those prefixes lets tools that group by location
(such as `get_energy_summary`) report them under the instance they come from
instead of the local area registry.

Comma-separated. Each item is either a name, in which case the prefix defaults to
`sensor.<name>_`, or `name=prefix` when your entity IDs follow a different
convention:

```
annex,workshop=sensor.ws_
```

Leave it empty on a single-instance setup: nothing is then treated as remote and
grouping falls back entirely to the area registry.

### `alexa_keywords` (default: `echo,alexa`)

Comma-separated substrings that mark a media player as an Amazon Echo. Matching
players are announced to through `alexa_media` instead of the regular TTS
service, which is what `send_tts` and `broadcast_tts` rely on.

The defaults match how the Alexa Media Player integration names its entities. Add
your own if a speaker group is named after a room or the household rather than
after Alexa. Leave it empty to disable the detection entirely.

### `default_language` (default: empty)

`send_tts`, `broadcast_tts`, `process_conversation` and `create_assist_pipeline`
take an optional `language`. When a call omits it, the language is resolved in
this order:

1. this option, when set;
2. the language reported by `/api/config`;
3. English.

Leave it empty and step 2 usually does the right thing. Set it when the instance
should speak a language different from the one it is configured in — a common
case, because Home Assistant derives entity IDs from that setting, so many
instances are deliberately kept in English to obtain English entity IDs while
the people using them speak something else. The interface language you see in
the UI does not help here: it is a per-user profile preference and is not
exposed by the API.

---

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

---

## Available tools

| Category | Tools |
|---|---|
| Lights | `list_lights`, `set_light` |
| Switches | `list_switches`, `toggle_entity` |
| Climate | `list_climate`, `set_climate` |
| Covers | `list_covers`, `cover_control` |
| Fans | `list_fans`, `fan_control` |
| Locks | `list_locks`, `lock_control` |
| Media players | `list_media_players`, `media_player_control`, `search_and_play_media` |
| Vacuum | `get_vacuum_state`, `vacuum_control`, `vacuum_room` |
| Alarm | `get_alarm_state`, `alarm_control` |
| Cameras | `list_cameras`, `get_camera_snapshot`, `send_camera_snapshot` |
| Buttons / numbers / selects / text | `press_button`, `set_number`, `set_select`, `set_text` |
| Sensors | `list_sensors`, `get_states_by_domain` |
| Weather & sun | `get_weather`, `get_sun` |
| Energy | `get_energy`, `get_energy_summary` |
| Statistics | `get_statistics`, `get_statistics_summary` |
| Automations | `list_automations`, `get_automation`, `create_automation`, `create_automation_from_blueprint`, `delete_automation`, `trigger_automation`, `toggle_automation`, `get_automation_trace` |
| Scripts | `list_scripts`, `get_script`, `create_script`, `delete_script`, `run_script` |
| Scenes | `list_scenes`, `create_scene`, `delete_scene`, `activate_scene` |
| Helpers | `list_helpers`, `create_helper`, `set_helper`, `delete_helper`, `counter_control`, `timer_control` |
| Template sensors | `create_template_sensor`, `delete_template_sensor` |
| Groups | `list_groups`, `create_group`, `update_group`, `delete_group` |
| Schedules | `list_schedules` |
| Blueprints | `list_blueprints`, `import_blueprint` |
| Webhooks | `trigger_webhook` |
| Areas | `list_areas`, `create_area`, `update_area`, `delete_area`, `set_entity_area` |
| Floors | `list_floors`, `create_floor`, `delete_floor`, `set_area_floor` |
| Labels | `list_labels`, `create_label`, `update_label`, `delete_label`, `get_entity_labels`, `set_entity_labels`, `bulk_set_entity_labels` |
| Devices | `list_devices`, `get_device`, `list_device_actions`, `list_device_conditions`, `list_device_triggers` |
| Entity registry | `get_entity`, `get_entity_registry`, `rename_entity`, `enable_entity`, `disable_entity`, `set_entity_area`, `get_entity_dependencies`, `get_entity_exposure`, `list_entities_by_integration`, `search_entities` |
| Persons | `list_persons`, `create_person`, `update_person`, `delete_person` |
| Users | `list_users`, `create_user`, `update_user`, `delete_user` |
| Tags | `list_tags`, `create_tag`, `update_tag`, `delete_tag` |
| Zones | `list_zones` |
| Calendar | `list_calendars`, `get_calendar_events`, `add_calendar_event` |
| To-do lists | `list_todo_lists`, `get_todo_items`, `add_todo_item`, `update_todo_item`, `remove_todo_item` |
| Dashboards | `list_dashboards`, `create_dashboard`, `get_dashboard`, `update_dashboard`, `update_dashboard_config`, `delete_dashboard`, `list_lovelace_resources`, `add_lovelace_resource`, `remove_lovelace_resource` |
| Add-ons | `list_addons`, `get_addon`, `start_addon`, `stop_addon`, `restart_addon`, `get_addon_logs`, `call_addon_api` |
| System | `get_config`, `get_supervisor_info`, `get_system_health`, `list_updates`, `apply_update`, `list_backups`, `create_backup`, `restart_homeassistant`, `reload_integration` |
| Repairs & config flows | `list_repairs`, `list_config_entries`, `list_config_flows`, `dismiss_config_flow` |
| HACS | `hacs_info`, `list_hacs_repos`, `get_hacs_repo`, `install_hacs_repo`, `remove_hacs_repo`, `search_hacs`, `add_hacs_custom_repo` |
| Assist | `list_assist_pipelines`, `create_assist_pipeline`, `update_assist_pipeline`, `delete_assist_pipeline`, `set_preferred_assist_pipeline`, `process_conversation` |
| Notifications | `list_notify_services`, `send_notification`, `send_notification_with_buttons`, `send_tts`, `broadcast_tts`, `send_photo`, `send_camera_snapshot` |
| Persistent notifications | `list_persistent_notifications`, `create_persistent_notification`, `dismiss_persistent_notification` |
| Alerts | `list_alerts`, `toggle_alert`, `acknowledge_alert` |
| Diagnostics | `get_history`, `get_logbook`, `get_error_log`, `list_services`, `call_service`, `render_template`, `fire_event`, `get_live_context` |

---

## Status dashboard

The add-on includes a built-in web UI accessible directly from the Home Assistant sidebar (via ingress — no extra port or reverse proxy needed).

Click **HA MCP Server** in the sidebar or open it from the add-on page via **Open Web UI**.

| Card | Content |
|------|---------|
| **HA Status** | Connection state, version, location, timezone, API latency |
| **MCP Server** | Port, auth status, tool count, prompt count, total calls |
| **Server** | Add-on version, uptime |
| **Live** | Entity count, lights on, alarm state |
| **Last Activity** | Most recently called tool, timestamp, latency, call count |
| **Recent Errors** | Last 20 tool errors with tool name, time, and message |
| **Top Tools** | Bar chart of most-called tools this session |
| **Tools / Prompts** | Full collapsible lists with descriptions |

The dashboard refreshes automatically every 30 seconds. Stats reset on add-on restart.

### Ports

| Port | Purpose |
|------|---------|
| `47821` | MCP HTTP server — used by Claude Code |
| `47822` | Status web UI — served via HA ingress (sidebar) |

The web UI port is internal only and never needs to be opened through your firewall or reverse proxy.

---

## Notes

- No token configuration needed — the add-on uses the Supervisor token automatically.
- The server accesses HA internally via the Supervisor proxy (`http://supervisor/core`), so REST and WebSocket both work without a long-lived access token.
- The MCP endpoint is served at `/` — compatible with reverse proxies that strip the path prefix.

---

## Compatibility

| Platform | Supported |
|---|---|
| Home Assistant OS | Yes |
| Home Assistant Supervised | Yes |
| Home Assistant Container | No |
| Home Assistant Core | No |

---

## Disclaimer

This is an unofficial Home Assistant add-on.
Not affiliated with the Home Assistant project or Anthropic.
