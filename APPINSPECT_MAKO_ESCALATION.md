# AppInspect UCC template policy note

REST Profiler 1.1.0 is generated with Splunk UCC Framework 6.5.3. Its
`appserver/templates/base.html` is a static UCC loader with no Mako expressions,
Python blocks, or custom CherryPy controller code.

Splunk AppInspect 4.3.0 nevertheless reports one `future_failure`:

```text
check_for_custom_mako_templates
```

The report contains 0 errors and 0 current failures. On 20 August 2026, the
Splunkbase Team stated that four checks related to Mako templates, CherryPy
controllers, and UCC versions will remain warnings, will not remove Splunk
Cloud compatibility, and require no action at this time. The public copy of
that notice is recorded in
[splunk/addonfactory-ucc-generator#2086](https://github.com/splunk/addonfactory-ucc-generator/issues/2086#issuecomment-5350200104).

The repository policy evaluator accepts only the four checks named in that
notice. All other AppInspect errors, failures, and future failures continue to
block release publication.

## Reproduce

```bash
make package VERSION=1.1.0
make appinspect-only VERSION=1.1.0
python3 scripts/evaluate_appinspect.py dist/appinspect-1.1.0.json
```

The native AppInspect exit code remains recorded in
`dist/appinspect-1.1.0.exit-code`; policy acceptance does not alter or conceal
that diagnostic result.
