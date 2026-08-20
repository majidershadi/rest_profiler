# Publishing 1.1.0

## Release validation

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-build.txt
python -m unittest discover -s tests -v
make release VERSION=1.1.0
```

The release target builds, verifies, packages, checksums, runs AppInspect, and
applies `scripts/evaluate_appinspect.py` as the policy gate.

Splunk's [20 August 2026 enforcement update](https://github.com/splunk/addonfactory-ucc-generator/issues/2086#issuecomment-5350200104)
keeps these four checks as non-enforcing warnings:

- `check_for_custom_mako_templates`
- `check_for_existence_of_python_code_block_in_mako_template`
- `check_cherrypy_controllers`
- `check_for_ucc_framework_version`

Only those names may be accepted as `future_failure`. Any AppInspect error,
failure, or unlisted future failure blocks publication.

## GitHub release

After the policy gate passes, merge the release commit to `main`, create the
stable tag, and publish the verified archive, checksum, and AppInspect JSON:

```bash
git tag v1.1.0
git push origin main v1.1.0
```

The tag workflow uses `release-notes/1.1.0.md` and publishes a stable GitHub
release. The packaged Splunk version and tag version are both `1.1.0`.

## Splunkbase release

Upload `dist/rest_profiler-1.1.0.tar.gz` and use the prepared store copy in
`SPLUNKBASE_1.1.0.md`. Retain `dist/SHA256SUMS.txt` and
`dist/appinspect-1.1.0.json` with the release records.

## Native AppInspect status

`dist/appinspect-1.1.0.exit-code` preserves the native AppInspect status. A
nonzero native code is not hidden: the policy evaluator must confirm that the
report contains no current errors or failures and only explicitly deferred
future findings.
