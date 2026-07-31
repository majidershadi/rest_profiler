# Publishing 1.0.1

## Local preflight

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-build.txt
make help
make release VERSION=1.0.1
```

`make release` is a hard gate: it builds, verifies, packages, checksums, and runs
AppInspect. Do not publish unless it exits successfully.

For diagnosis while AppInspect is failing:

```bash
make clean
make package VERSION=1.0.1
make appinspect-only VERSION=1.0.1
```

Review `dist/appinspect-1.0.1.json`. The current UCC/AppInspect template mismatch is
documented in `APPINSPECT_MAKO_ESCALATION.md`.

## GitHub release

Commit the release files and push `main`. Create the `v1.0.1` tag only after the
AppInspect gate passes:

```bash
git add .
git commit -m "build: add Makefile release interface"
git push origin main
git tag -a v1.0.1 -m "REST Profiler for Splunk 1.0.1"
git push origin v1.0.1
```

Use **Actions → Build and publish release → Run workflow** to validate `1.0.1` from
`main` without moving a tag. The workflow always preserves the package, checksum, and
AppInspect JSON as a workflow artifact. It creates the GitHub Release only for a tag
push and only when AppInspect exits with code 0.

## Splunkbase release

Upload the exact `rest_profiler-1.0.1.tar.gz` produced by a successful workflow as a
new Splunkbase release. Use `release-notes/1.0.1.md`. Splunkbase then runs its own
current Cloud evaluation.
