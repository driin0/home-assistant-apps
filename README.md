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

## Apps

### [Zoraxy](./zoraxy)

![Supports aarch64 Architecture][aarch64-shield]
![Supports amd64 Architecture][amd64-shield]

A general purpose HTTP reverse proxy and forwarding tool, with ACME auto TLS,
a plugin system and a web management interface. Packaged on the official Home
Assistant base image with native `bashio` configuration handling and prebuilt
multi-architecture images.

## Licence

AGPL-3.0. Zoraxy itself is AGPL-3.0 software by Toby Chui; see [NOTICE](./NOTICE)
for the full attribution.

[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
