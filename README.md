# REST Profiler for Splunk

Define reusable, fully-featured REST API request **profiles** and execute them as Splunk alert actions, ad-hoc searches, or one-off tests — with encrypted secret storage, multiple authentication methods, per-row result delivery, and the reliability plumbing (timeout, retry, validation, proxy) you'd otherwise write by hand.

- **Splunk compatibility:** Splunk Enterprise 10.x
- **Platform:** Linux
- **License:** Apache-2.0
- **Built with:** the Splunk UCC framework 6.5.3
- **Python:** compatible with the supported Splunk Python runtimes

---

## Table of contents

- [Why](#why)
- [Concepts](#concepts)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Creating a profile](#creating-a-profile)
- [Authentication](#authentication)
- [TLS and certificates](#tls-and-certificates)
- [Result delivery](#result-delivery)
- [Reliability controls](#reliability-controls)
- [Proxy support](#proxy-support)
- [The search command](#the-search-command)
- [Logging and troubleshooting](#logging-and-troubleshooting)
- [Building from source](#building-from-source)
- [Security model](#security-model)
- [License](#license)

---

## Release status

Current prerelease: **1.1.0-rc.1** (2026-08-14). This release candidate encrypts complete saved request bodies at rest and adds `§secret§` markers so sensitive body fragments are masked in previews and removed from the transmitted payload.

Release artifacts are built and checked from a Git tag by `.github/workflows/release.yml`. See [`release-notes/1.1.0-rc.1.md`](release-notes/1.1.0-rc.1.md) for the release notes.

---

## Why

Splunk ships a generic HTTP alert action, but it expects the full request — endpoint, headers, body, credentials — to be typed into every alert as free text, in clear text, with no way to verify it before it fires. REST Profiler replaces that with a **profile**: a complete, named, reusable request whose secrets are encrypted and which you can preview and test before any alert depends on it.

---

## Concepts

A **profile** is a saved HTTP request definition. You create profiles on the add-on's configuration page, then reference them by name from:

- the **alert action** "REST Profiler: Send request",
- the **`| restprofilersend`** search command, and
- the **Preview** and **Test send** buttons on the configuration page.

Because all three execution paths share one underlying client, a profile behaves identically wherever it runs.

---

## Features

- **Profiles:** create, edit, clone, delete.
- **All HTTP methods:** GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS.
- **Preview:** renders the exact outgoing request with secrets masked, before sending.
- **Test send:** fires the request live and returns the full response.
- **Authentication:** none, HTTP Basic, token/bearer, and mutual TLS (client certificate).
- **Encrypted secrets:** request bodies, passwords, tokens, certificates, key passphrases, and proxy passwords are stored encrypted in Splunk secure storage; `§secret§` body fragments and authentication headers are masked in previews and logs.
- **Per-row result delivery:** send each triggering result row as a JSON, XML, or form-urlencoded body, as URL query parameters, or via a custom `$field$` template.
- **Reliability:** request timeout, retry with exponential backoff, rate limiting, and response validation.
- **Proxy:** HTTP/HTTPS/SOCKS5 with a separate proxy authentication option.
- **Search command:** `| restprofilersend` for ad-hoc and scheduled execution.
- **Observability:** monitoring dashboard, configurable log level, optional response indexing.

---

## Architecture

REST Profiler is generated with the Splunk UCC framework and is organized in three layers.

**1. Configuration layer.** Profiles are stored as stanzas in `rest_profiler_profile.conf` and managed through a React-based configuration page backed by Splunk REST endpoints. Every field is validated client-side and server-side. The entire UI — fields, conditional visibility, validation — is declared in a single `globalConfig.json`; there is no hand-maintained REST handler code.

**2. Secret storage layer.** Fields marked as secrets are never written to the profile stanza in clear text. They are stored encrypted in **Splunk secure storage** (`passwords.conf`, via the `storage/passwords` endpoint), encrypted at rest with the instance `splunk.secret`, and decrypted only at execution time inside `splunkd`. The add-on intentionally uses secure storage rather than the KV Store, because secure storage provides at-rest encryption the KV Store does not.

**3. Execution layer.** A single shared Python client composes and sends every request — for Preview/Test, for the search command, and for the alert action — so behavior is identical across all entry points. The alert action reads the triggering results and, when result-sending is enabled, issues one request per row with the configured serialization.

```
Configuration page ─┐
Search command      ├─→  shared client  ─→  compose request ─→ send ─→ result
Alert action       ─┘          │
                               └─ decrypts secrets from secure storage at send time
```

---

## Installation

### From Splunkbase (Web UI)

*Apps → Find More Apps*, search **REST Profiler**, install, restart Splunk when prompted.

### From a file (Web UI)

*Apps → Manage Apps → Install app from file*, choose the `.tar.gz`, install, restart.

### From the CLI

```bash
$SPLUNK_HOME/bin/splunk install app rest_profiler-1.1.0.tar.gz -auth <admin>:<password>
$SPLUNK_HOME/bin/splunk restart
```

A restart after installation is recommended so the alert action, search command, and REST endpoints register cleanly.

### Upgrading

Back up your configuration first — copy `$SPLUNK_HOME/etc/apps/rest_profiler/local/` (your profiles and settings) somewhere safe — then install the new version over the existing one and restart. Your `local/` configuration and encrypted secrets are preserved across upgrades.

---

## Creating a profile

Go to the app, open **Configuration**, and add a profile. The core fields:

| Field | Notes |
|---|---|
| Name | Unique identifier for the profile |
| URL | Full request URL, e.g. `https://api.example.com/v1/ingest` |
| HTTP method | GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS |
| Headers | One `Header: value` per line |
| Content type | Sets the `Content-Type` header for the body |
| Body | Request body for methods that carry one |
| Verify SSL certificate | Enabled by default; see [TLS and certificates](#tls-and-certificates) |

Use **Preview** to see the exact request (secrets masked), and **Test send** to fire it once and inspect the response.

The complete saved **Body** field is encrypted at rest through Splunk secure storage. To hide selected values in Preview as well, wrap them in section signs:

```json
{"username":"§api-user§","password":"§change-me§","scope":"events:write"}
```

Preview renders both marked values as `********`. A live request sends the values without the section signs. Use `§§` when the outgoing body needs a literal `§`. An unmatched marker stops the request with a safe validation error that does not echo the body.

---

## Authentication

Set per profile. All secret values are stored encrypted.

| Method | Fields |
|---|---|
| None | — |
| HTTP Basic | Username, encrypted password |
| Token / Bearer | Header name (default `Authorization`), prefix (default `Bearer`), encrypted token value |
| Client certificate (mTLS) | Base64-encoded combined PEM, optional encrypted key passphrase |

### Mutual TLS setup

Mutual TLS means both sides authenticate during the TLS handshake — the server presents its certificate as usual, and the client proves its identity with its own certificate and key. To configure it:

1. Combine your client certificate and private key into one PEM:
   ```bash
   cat client.crt client.key > client_combined.pem
   ```
2. Base64-encode it as a single line:
   ```bash
   base64 -w0 client_combined.pem
   ```
3. In the profile, set **Authentication method = Client certificate (mTLS)** and paste the base64 string into **Client certificate (base64 PEM)**.
4. If the key is passphrase-protected, enter the passphrase in **Client key passphrase**.
5. Use **Test send** to verify the handshake.

At send time the certificate is decrypted, written to a temporary file readable only by the Splunk user, used for the handshake, and removed immediately afterward.

---

## TLS and certificates

Each profile has a **Verify SSL certificate** switch (enabled by default). The HTTP engine validates the server's certificate chain against the `certifi` CA bundle shipped with the add-on, so endpoints signed by public CAs work out of the box.

To trust a **private/internal CA**, point the engine at your own PEM bundle via `REQUESTS_CA_BUNDLE` in `$SPLUNK_HOME/etc/splunk-launch.conf`:

```
REQUESTS_CA_BUNDLE=/opt/splunk/etc/auth/mycerts/internal-ca-bundle.pem
```

To use the **operating-system trust store** instead, point the same variable at it:

```
# Debian/Ubuntu
REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
# RHEL-family
REQUESTS_CA_BUNDLE=/etc/pki/tls/certs/ca-bundle.crt
```

Restart Splunk after changing `splunk-launch.conf`. Verification can be disabled per profile for trusted internal endpoints with self-signed certificates.

References: Splunk [TLS overview](https://docs.splunk.com/Documentation/Splunk/latest/Security/AboutsecuringyourSplunkconfigurationwithSSL) and [`splunk-launch.conf`](https://docs.splunk.com/Documentation/Splunk/latest/Admin/Splunklaunchconf).

---

## Result delivery

When **Send triggering results** is enabled on a profile, the alert sends **one request per triggering row** (capped at 1000 rows per trigger). Choose the format per profile:

| Format | Output | Content-Type |
|---|---|---|
| JSON body | `{"field":"value", ...}` | `application/json` |
| XML body | `<event><field name="...">value</field>...</event>` | `application/xml` |
| Form body | `field=value&...` | `application/x-www-form-urlencoded` |
| Query parameters | appended to the URL | (unchanged) |
| Custom template | your Body/URL with `$field$` tokens substituted | (unchanged) |

**Result fields to include** selects and orders the fields (empty = all non-internal fields). Content-Type is set automatically per format and can be overridden by an explicit Content-Type on the profile.

### Templating

With the Custom template format, `$fieldname$` tokens in the **Body** and **URL** are replaced with the triggering row's values. `$$` produces a literal `$`. Unknown tokens are left unchanged.

```
Body:  {"host":"$host$","severity":"$severity$","msg":"$_raw$"}
URL:   https://api.example.com/incidents/$incident_id$
```

> Note: result delivery applies when an alert fires (where triggering rows exist). The Preview button and the search command operate on the static request definition.

---

## Reliability controls

| Control | Behavior |
|---|---|
| Request timeout | 1–600 seconds (default 30) |
| Retry attempts | 0–5 (default 0 = a single attempt) |
| Retry backoff | Initial wait, doubled each attempt (exponential) |
| Retry on | Connection errors only · also HTTP 5xx · also HTTP 429 |
| Rate limit | Minimum seconds between consecutive per-row requests |
| Response validation | Expected status codes (e.g. `200-299,302`) and/or required body substring |

TLS handshake failures are never retried (they don't self-heal). With response validation configured, a request counts as successful only when the status and body criteria are both met; with it empty, the default rule (any response below 400) applies.

---

## Proxy support

Per profile, route requests through an HTTP, HTTPS, or SOCKS5 proxy:

- **Proxy URL** — e.g. `http://proxy.corp:3128` or `socks5h://proxy.corp:1080`
- **Proxy authentication** — None, or Username/encrypted password (separate from the endpoint's own authentication)

---

## The search command

```
| restprofilersend profile="<name>" mode=preview
| restprofilersend profile="<name>" mode=send
```

`mode=preview` returns the composed request (secrets masked); `mode=send` executes it and returns the response as a single event with status, headers, timing, and a truncated body.

---

## Logging and troubleshooting

The add-on logs to `$SPLUNK_HOME/var/log/splunk/rest_profiler.log`, indexed into `_internal`:

```spl
index=_internal source=*rest_profiler*.log*
index=_internal source=*splunkd.log* sendmodalert action=rest_profiler_send_alert
```

Raise verbosity in **Configuration → Logging** (set DEBUG, reproduce, set back to INFO).

**Common checks**
- Alert sends nothing → open the alert, confirm a profile is selected, re-save it, then check the searches above after the next trigger.
- Connection/TLS errors → reproduce interactively with **Test send**; for private CAs see [TLS and certificates](#tls-and-certificates).
- A profile won't save → the message names the failing field; required fields depend on the selected authentication, proxy, and result-delivery options.

**After an upgrade misbehaves**, do a clean reinstall: back up `local/`, remove the app, **restart**, install the new package, **restart again**, restore `local/`. The double restart clears cached REST handlers and the previous Python library set.

---

## Building from source

Install the pinned release tools, then use the repository Makefile as the single build interface:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-build.txt
make package VERSION=1.1.0
make appinspect-only VERSION=1.1.0
```

`make release VERSION=1.1.0` performs a clean package build and enforces the AppInspect gate. The compatibility wrapper `./scripts/build_release.sh 1.1.0` invokes the same target.

> The bundled Python libraries target the Splunk runtime (Python 3.9 on Splunk 10.0, 3.13 on 10.2+). `package/lib/requirements.txt` pins versions accordingly and forces a pure-Python install of any dependency that would otherwise vendor an architecture-specific binary. Don't unpin them without checking your Splunk's bundled Python version.

---

## Security model

- Complete request bodies and credential fields are stored encrypted in Splunk secure storage (`passwords.conf`), never in clear text in the profile stanza.
- Body fragments wrapped as `§secret§` are masked in previews; delimiters are removed only while composing a live request inside `splunkd`.
- Authentication values are decrypted only at execution time. `Authorization`, `Proxy-Authorization`, and configured custom token headers are masked wherever request headers are returned or rendered.
- Client certificates are written to temporary, owner-only files that are removed immediately after the TLS handshake.
- SSL verification is on by default and configurable per profile.

---

## License

Apache License 2.0. See [`LICENSE`](LICENSE).

## Contact

Issues and feature requests: open a GitHub issue, or reach out via the channels on the Splunkbase listing.
