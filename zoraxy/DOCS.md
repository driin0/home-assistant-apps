# Zoraxy — Home Assistant App

> **Upstream project**
>
> Zoraxy is created and maintained by [@tobychui](https://github.com/tobychui) and
> licensed under AGPL-3.0. This repository only packages it as a Home Assistant
> app; it is not affiliated with, nor endorsed by, the Zoraxy project.
>
> Questions about **Zoraxy features or behaviour** belong upstream:
> <https://github.com/tobychui/zoraxy/wiki>.
> Please use this repository's issue tracker only for problems with the **Home
> Assistant packaging** — installation, options, startup, images.

## Configuration

### Basic Options

| Option      | Default | Description |
|-------------|---------|-------------|
| `noauth`    | `false` | Disable authentication for the management interface |
| `fastgeoip` | `true`  | Enable high-speed GeoIP lookup |

### Advanced Options

| Option                           | Default   | Description |
|----------------------------------|-----------|-------------|
| `plugin`                         | `plugin`  | Plugin directory (relative to `/config`) |
| `tz`                             | `Etc/UTC` | Timezone (tzdata format) |
| `autorenew`                      | `86400`   | ACME certificate renew check interval (seconds) |
| `earlyrenew`                     | `30`      | Days before expiry to trigger certificate renewal |
| `cfgupgrade`                     | `true`    | Auto-upgrade config on breaking changes |
| `db`                             | `auto`    | Database backend (`auto`, `leveldb`, `boltdb`) |
| `enablelog`                      | `true`    | Enable system-wide logging |
| `mdns`                           | `true`    | Enable mDNS scanner and transponder |
| `mdnsname`                       |           | Custom mDNS hostname (leave empty for default) |
| `sshlb`                          | `false`   | Enable loopback SSH (dangerous) |
| `acmetestmode`                   | `false`   | Run ACME in test/staging mode |
| `update_geoip`                   | `false`   | Download latest GeoIP data, then start normally |
| `version`                        | `false`   | Show version and exit |
| `webroot`                        | `./www`   | Static web server root folder |
| `lego_azure_bypass_deprecation`  | `false`   | Re-enable the deprecated `azure` DNS provider for ACME |

### Azure DNS Options (ACME)

These options are exported as environment variables and read by Zoraxy's built-in
ACME client (lego) when **AuthMethod** is set to `env` in Zoraxy's DNS credentials
form.

| Option | Description |
|--------|-------------|
| `azure_client_id` | Azure App Registration Application (client) ID — not the Object ID |
| `azure_tenant_id` | Azure Directory (tenant) ID |
| `azure_subscription_id` | Azure Subscription ID containing the DNS zones |
| `azure_client_certificate_path` | Path to the PFX certificate inside the container, e.g. `/config/certs/azure-dns.pfx` |
| `azure_client_secret` | Client secret (alternative to the certificate) |

The Azure App Registration needs the `DNS Zone Contributor` role on every managed
DNS zone, plus `Reader` on the subscription — lego uses Azure Resource Graph to
discover zones.

**Certificate authentication.** The PFX must be generated with legacy SHA1/3DES
algorithms; Go's PKCS12 parser does not accept the modern defaults.

```bash
openssl req -x509 -newkey rsa:4096 -keyout azure-dns.key \
  -out azure-dns.crt -days 3650 -nodes \
  -subj "/CN=zoraxy-azure-dns"

openssl pkcs12 -export \
  -out azure-dns.pfx \
  -inkey azure-dns.key \
  -in azure-dns.crt \
  -keypbe PBE-SHA1-3DES \
  -certpbe PBE-SHA1-3DES \
  -macalg SHA1 \
  -passout pass:
```

Upload `azure-dns.crt` (not the `.pfx`) to the App Registration under
**Certificates & secrets → Certificates**. Copy `azure-dns.pfx` into a `certs/`
folder inside this app's directory under `/addon_configs/` on the Home Assistant
host — the exact directory name is prefixed with the repository identifier, so
read it from the app's Configuration tab rather than guessing it. Inside the
container that path is always `/config`, so set `azure_client_certificate_path`
to `/config/certs/azure-dns.pfx`.

In Zoraxy, under **TLS/SSL Certificates → ACME Tools → DNS Provider → Azure DNS**,
set `AuthMethod` to `env` and leave `SubscriptionID` empty — it comes from the
environment variable. `ClientCertificate` is **not** a valid `AuthMethod` value in
lego and is silently ignored.

## Persistent Storage

All configuration is stored under `/config`, mapped to the app's persistent config
directory and preserved across restarts and updates. With `plugin` left at its
default, plugins live in `/config/plugin`.

## Exposed Ports

| Port | Purpose |
|------|---------|
| `8000` | Web management interface |
| `80`   | HTTP reverse proxy |
| `443`  | HTTPS reverse proxy |

## Security Recommendations

- Do not enable `noauth` on an instance reachable from the internet.
- Do not enable `sshlb` unless strictly necessary.
- Use firewall rules if you expose ports 80 and 443.

## Support

Packaging issues: <https://github.com/driin0/home-assistant-apps/issues>.
Zoraxy functionality: <https://github.com/tobychui/zoraxy>.

## Licence

AGPL-3.0. See `LICENSE` and `NOTICE` at the repository root.
