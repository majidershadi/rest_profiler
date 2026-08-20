# Splunkbase update copy for REST Profiler 1.1.0

## Short release summary

REST Profiler 1.1.0 protects secrets in POST, PUT, and PATCH request bodies.
Complete saved bodies are encrypted at rest in Splunk secure storage, while
optional `§secret§` markers hide selected values in Preview. The release also
masks custom token, Authorization, and Proxy-Authorization headers.

## What's new

- **Encrypted request bodies:** the complete saved Body field is protected by
  Splunk secure storage and is not stored as clear text in the profile stanza.
- **Selective preview masking:** wrap a sensitive body fragment as `§secret§`;
  Preview displays `********`, while the live request sends `secret` without
  the delimiters.
- **Safe delimiter handling:** `§§` sends a literal section sign. An unmatched
  marker blocks the request without exposing its body in the error.
- **Broader header protection:** configured custom token headers,
  `Authorization`, and `Proxy-Authorization` are masked in previews, returned
  request metadata, and logs.
- **No profile-format migration:** existing profiles remain readable. Re-save
  an existing profile once to migrate a previously stored body into encrypted
  storage.

## Detailed store description

REST Profiler lets Splunk administrators define reusable HTTP request profiles
and execute them from alert actions, searches, or interactive tests. A profile
can contain the URL, method, headers, content type, request body,
authentication, TLS settings, proxy settings, timeout, retry behavior, rate
limits, and response validation rules.

Version 1.1.0 strengthens handling of credentials embedded in request bodies.
The complete saved Body field now uses Splunk's encrypted secure-storage
mechanism, the same platform mechanism used for passwords and tokens. For safe
review and troubleshooting, administrators can additionally mark individual
body fragments with section signs. Marked fragments are replaced with
`********` in Preview, while the original value is restored only inside
`splunkd` when a live request is composed.

REST Profiler supports HTTP Basic, bearer/custom token, and mutual-TLS
authentication; HTTP, HTTPS, and SOCKS5 proxies; JSON, XML, form, query, and
custom-template result delivery; and per-row alert delivery with response
indexing and monitoring.

## Upgrade instructions

1. Back up `$SPLUNK_HOME/etc/apps/rest_profiler/local/`.
2. Install `rest_profiler-1.1.0.tar.gz` over the existing version.
3. Restart Splunk.
4. Edit and save existing profiles that contain a Body value once, so that
   value is migrated into encrypted secure storage.
5. Use Preview and Test send to verify the profile before enabling alerts.

## AppInspect note

AppInspect 4.3.0 reports 0 errors and 0 failures. Its single future finding is
the UCC-generated static-template check covered by Splunk's 20 August 2026
enforcement update. Splunk states that this check remains a warning, does not
remove Splunk Cloud compatibility, and requires no action at this time.
