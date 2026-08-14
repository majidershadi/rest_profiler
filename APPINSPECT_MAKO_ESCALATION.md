# AppInspect `check_for_custom_mako_templates` escalation

## Current blocker

REST Profiler 1.1.0 (GitHub prerelease `v1.1.0-rc.1`) is generated with Splunk UCC Framework 6.5.3. The generated file
`appserver/templates/base.html` is plain static HTML and contains no Mako or CherryPy
syntax. Nevertheless, Splunk AppInspect 4.3.0 reports it as a `future_failure` under
`check_for_custom_mako_templates` solely because it remains under
`appserver/templates/`.

The generated views reference this loader directly:

- `default/data/ui/views/configuration.xml`
- `default/data/ui/views/dashboard.xml`

Removing `base.html` without changing the UCC-generated view architecture would break
both pages. The release pipeline therefore does not delete or suppress this file.

## Reproduction

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-build.txt
make clean
make package VERSION=1.1.0
make appinspect-only VERSION=1.1.0
```

Expected current result: AppInspect exits with code 104 and reports 0 errors,
0 failures, 1 `future_failure` for `appserver/templates/base.html`, 11 warnings,
and 114 successful checks.

## Suggested support message

Subject: UCC 6.5.3-generated static base.html is flagged by AppInspect 4.3.0

REST Profiler for Splunk 1.1.0 is generated with
`splunk_add_on_ucc_framework==6.5.3` and inspected with
`splunk-appinspect==4.3.0`. UCC generates a plain static
`appserver/templates/base.html` loader with no Mako/CherryPy expressions, but the
current `check_for_custom_mako_templates` reports that file as a `future_failure`.
The generated configuration and dashboard views reference the loader, so removing it
breaks the UCC UI.

Please confirm the supported UCC output/layout for the enhanced Cloud vetting check,
or whether this UCC-generated static loader should be exempted. The AppInspect JSON
report and generated package can be attached to the case.

Contact supplied in the Splunkbase notification: `devsupport-splunk@cisco.com`.
