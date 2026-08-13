# driin0's Home Assistant Apps

A Home Assistant app repository (formerly "add-on repository").

> **Zoraxy is created and maintained by [@tobychui](https://github.com/tobychui).**
> This repository only packages it as a Home Assistant app. It is not affiliated
> with, nor endorsed by, the Zoraxy project or the Home Assistant project.

## Installation

[![Open your Home Assistant instance and show the add app repository dialog with a specific repository URL pre-filled.](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fdriin0%2Fhome-assistant-apps)

Or add it manually:

1. Go to **Settings → Add-ons → Add-on Store**
2. Click **⋮ → Repositories**
3. Paste `https://github.com/driin0/home-assistant-apps` and confirm
4. Install the app

Both apps ship prebuilt multi-architecture images, so installing pulls an image
rather than building one on your hardware.

## Apps

### [Zoraxy](./zoraxy)

![Supports aarch64 Architecture][aarch64-shield]
![Supports amd64 Architecture][amd64-shield]

A general purpose HTTP reverse proxy and forwarding tool, with ACME auto TLS,
a plugin system and a web management interface. Packaged on the official Home
Assistant base image with native `bashio` configuration handling and prebuilt
multi-architecture images.

### [HA MCP Server](./ha-mcp-server)

![Supports aarch64 Architecture][aarch64-shield]
![Supports amd64 Architecture][amd64-shield]

Exposes Home Assistant's REST and WebSocket APIs as **182 MCP tools**, so that
an MCP client — Claude Code among others — can drive the instance directly:
lights, climate, covers, media, alarm and cameras; automations, scripts, scenes,
helpers and dashboards; the area, floor, label, device and entity registries;
add-ons, HACS, backups and system health; history, logbook, statistics and
energy.

Authentication is a bearer token, and the add-on reaches Home Assistant through
the Supervisor, so no long-lived access token has to be created. A status
dashboard is available in the sidebar through ingress.

**It can also delete things** — automations, dashboards, helpers, users. Every
tool was exercised against a live instance before release, but treat it as
what it is: a broad, powerful interface to your home.

### [Iliad Tools](./iliad-tools)

![Supports aarch64 Architecture][aarch64-shield]
![Supports amd64 Architecture][amd64-shield]

An administration portal for **iliadbox**, the router Iliad sells in Italy,
which runs Freebox OS. Static DHCP leases, LAN devices with Wake on LAN, WAN
status with a live bandwidth chart and RRD history, port forwarding, Wi-Fi with
a neighbouring-network survey, WireGuard VPN with per-router profiles, and a
generator for Asterisk configuration — the Iliad SIP trunk, internal extensions
and multi-tenant 3CX trunks — that produces an archive ready to apply.

Router credentials are encrypted at rest with AES-256-GCM behind a master
password. **The interface is in Italian**, since the router is only sold there.

The application itself lives in
[driin0/iliad-tools](https://github.com/driin0/iliad-tools); this app ships its
image for Home Assistant.

## Licence

AGPL-3.0.

Zoraxy itself is AGPL-3.0 software by Toby Chui; see [NOTICE](./NOTICE) for the
full attribution. HA MCP Server is original work in this repository.

## Trademarks

Home Assistant and its logo are trademarks of the
[Open Home Foundation](https://www.openhomefoundation.org/). The Model Context
Protocol and its mark belong to [Anthropic](https://www.anthropic.com/). App
icons and logos reference those marks to show what each app connects, not to
imply that either project produced or endorsed anything here. All trademarks
are the property of their respective owners.

[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
