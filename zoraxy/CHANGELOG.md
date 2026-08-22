# Changelog

## 3.3.4-1

- Zoraxy v3.3.4 (stable)
- **The configuration database is migrated from v333 to v334 on first start, and
  the migration only runs forward.** Back up the app's directory under
  `/addon_configs/` before updating; rolling back to 3.3.3 means restoring that
  backup, not reinstalling the previous version.
- Upstream moved its ACME client from lego v4 to v5. The Azure DNS provider used
  by this app (`azuredns`) is unaffected — certificate issuance and renewal were
  verified against the production Let's Encrypt endpoint before this release.
- **Removed the `lego_azure_bypass_deprecation` option.** lego v5 deleted the
  deprecated `azure` DNS provider along with the `LEGO_AZURE_BYPASS_DEPRECATION`
  variable it read, so the option had nothing left to switch on. If it is set in
  your configuration, Home Assistant reports `Option '...' does not exist in the
  schema` once and drops the value; remove it and the warning goes away. Anyone
  still on the `azure` provider must migrate to `azuredns`.
- New option `stats_max_entries`, a soft cap on the per-dimension statistics
  maps. It defaults to `20000` here rather than upstream's unlimited `0`, because
  unbounded maps are a memory ceiling that gives no warning on a small device.
  Set it to `0` for upstream behaviour.
- New HTTP/2 options for the inbound TLS listener: `disablehttp2`,
  `h2_conn_buffer`, `h2_stream_buffer` and `h2_max_concurrent_streams`. All
  default to upstream's values, so nothing changes unless you set them. See
  `DOCS.md` — the two buffers silently ignore any value between 1 and 65535.

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
