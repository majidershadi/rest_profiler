REST Profiler for Splunk
========================

Author : majid ershadi
Website: https://majiershadi.github.io
License: Apache License 2.0

REST Profiler lets you define reusable REST API request profiles and execute
them as Splunk alert actions, ad-hoc searches, or one-off tests.

A profile describes a complete HTTP request: URL, method, custom headers,
content type, encrypted body, request timeout, retry policy with exponential backoff,
optional proxy (HTTP/HTTPS/SOCKS5 with separate proxy authentication),
response validation (expected status codes and body content), rate limiting,
SSL verification, and endpoint authentication (none, HTTP Basic, token/bearer,
or mutual TLS via client certificate). All secrets - passwords, tokens,
certificates, key passphrases, and complete request bodies - are stored
encrypted in Splunk secure storage (passwords.conf). Body fragments wrapped as
§secret§ and authentication headers are masked in previews and logs; the
section signs are removed before a live request is transmitted. Use §§ for a
literal section sign.

Highlights
----------
- Profiles: create, edit, clone, delete; per-row Preview (exact masked request)
  and live Test send.
- Alert action "REST Profiler: Send request": run a profile when an alert
  fires; optionally send the triggering result rows, one request per row, as a
  JSON / XML / form-urlencoded body, URL query parameters, or a custom
  $field$ template in the body and URL.
- Search command: | restprofilersend profile="<name>" mode=preview|send
- Monitoring dashboard, configurable log level, and a Search view.

Compatibility
-------------
Designed for Splunk Enterprise 10.x. Using earlier versions is not
recommended (Python runtime differences).

1.1.0-rc.1
----------
- Encrypts complete saved request bodies in Splunk secure storage.
- Masks §secret§ request-body fragments in previews and removes the markers
  before transmission.
- Masks configured custom token headers in returned request metadata.

1.0.1
-----
- Refreshed the UCC-managed static bootstrap for current Splunk Cloud vetting.
- No profile, alert-action, search-command, or saved-configuration changes.

1.0.0
-----
- First stable release.
