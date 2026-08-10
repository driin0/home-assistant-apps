# Changelog

## 3.3.3-1

First public release.

- Zoraxy v3.3.3 (stable), binary taken unmodified from the official upstream image
- Runs as an s6 supervised service instead of a bare container command, so a crash
  is reported to Home Assistant instead of failing silently
- Built on the unified Home Assistant base image `ghcr.io/home-assistant/base:3.24`
- Distributed as prebuilt, cosign-signed multi-architecture images on GHCR — the
  app is no longer built on your device
- Licensed AGPL-3.0, matching upstream

### Previous history

These versions were released in the private repository this app originated from.

#### 3.3.3-1 (private)

- Updated to Zoraxy v3.3.3 (stable)
- Upstream highlights: removed deprecated SMTP feature, internal DB migrated to a
  maintained boltDB fork, new WebDAV server access plugin, custom URI for Uptime
  Monitor health checks, fixed ACME certificate request regression from rc2,
  listeners now enforce `ReadHeaderTimeout`/`IdleTimeout`

#### 3.3.2-3

- Added Azure DNS ACME options: `azure_client_id`, `azure_tenant_id`,
  `azure_subscription_id`, `azure_client_certificate_path`, `azure_client_secret`

#### 3.3.2-2

- Switched to the Home Assistant native base image
- Replaced the upstream `entrypoint.py` with a `bashio`-based startup script
- Config path moved from `/opt/zoraxy/config` to `/config`
- Added `update-ca-certificates` on startup
- Added the `-acmetestmode` flag
- Fixed `update_geoip`: updates then continues instead of exiting

#### 3.3.2-1

- Updated to Zoraxy v3.3.2 (stable)

#### 3.3.2-rc4-1

- Initial release, based on Zoraxy v3.3.2-rc4
- Persistent configuration via the `addon_config` map
- Safe optional flag handling (empty values are ignored)
- Support for the `LEGO_AZURE_BYPASS_DEPRECATION` environment variable
