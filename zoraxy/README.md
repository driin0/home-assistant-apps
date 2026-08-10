# Zoraxy — Home Assistant App

![Supports aarch64 Architecture](https://img.shields.io/badge/aarch64-yes-green.svg)
![Supports amd64 Architecture](https://img.shields.io/badge/amd64-yes-green.svg)
![License](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)

> **Zoraxy is created and maintained by [@tobychui](https://github.com/tobychui).**
> This repository only packages it as a Home Assistant app. It is not affiliated
> with, nor endorsed by, the Zoraxy project or the Home Assistant project.
>
> - Upstream project: <https://github.com/tobychui/zoraxy>
> - Upstream documentation: <https://github.com/tobychui/zoraxy/wiki>
> - Upstream container image: <https://hub.docker.com/r/zoraxydocker/zoraxy>

## About

Zoraxy is a general purpose HTTP reverse proxy and forwarding tool with ACME auto
TLS, a plugin system and a web management interface.

This app runs the official upstream Zoraxy binary on the Home Assistant base
image, supervised by s6, with all options exposed through the Home Assistant
configuration UI via `bashio`.

## Features

- Reverse proxy with ACME auto TLS and automatic certificate renewal
- Persistent configuration and plugins under the app config directory
- Optional mDNS scanner and transponder
- Fast GeoIP lookup
- Azure DNS credentials for the ACME DNS challenge
- Prebuilt multi-architecture images — no build on your device

## Installation

1. Go to **Settings → Add-ons → Add-on Store**
2. Click **⋮ → Repositories**
3. Paste `https://github.com/driin0/home-assistant-apps` and confirm
4. Install **Zoraxy**, configure the options, then start it

See [DOCS.md](./DOCS.md) for the full option reference.

## Compatibility

| Platform | Supported |
|----------|-----------|
| Home Assistant OS | ✅ |
| Home Assistant Supervised | ✅ |
| Home Assistant Container | ❌ |
| Home Assistant Core | ❌ |

## Development

To build locally instead of pulling the published image, comment out the `image:`
key in `config.yaml` — the Supervisor will then build the app on the device.
Remember to restore it before opening a pull request.

## Licence

AGPL-3.0. See [LICENSE](../LICENSE) and [NOTICE](../NOTICE).
