# Publishing 1.1.0-rc.1

## Local preflight

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-build.txt
make help
make release VERSION=1.1.0
```

`make release` is a hard gate: it builds, verifies, packages, checksums, and runs
AppInspect. Do not publish unless it exits successfully.

For diagnosis while AppInspect is failing:

```bash
make clean
make package VERSION=1.1.0
make appinspect-only VERSION=1.1.0
```

Review `dist/appinspect-1.1.0.json`. The current UCC/AppInspect template mismatch is
documented in `APPINSPECT_MAKO_ESCALATION.md`.

## GitHub release

Commit the release files and push `main`. Create the `v1.1.0-rc.1` tag only
after the unit, package, and AppInspect gates pass:

```bash
git add .
git commit -m "feat: encrypt and mask request body secrets"
git push origin main
git tag -a v1.1.0-rc.1 -m "REST Profiler for Splunk 1.1.0-rc.1"
git push origin v1.1.0-rc.1
```

Use **Actions → Build and publish release → Run workflow** to validate `1.1.0`
from `main` without moving a tag. The workflow always preserves the package,
checksum, and AppInspect JSON as a workflow artifact. A `vX.Y.Z-rc.N` tag
creates a GitHub prerelease only when AppInspect exits with code 0.

## Splunkbase release

Do not upload a release candidate to Splunkbase as the default release. After
prerelease validation, promote the same source as `v1.1.0`, rebuild
`rest_profiler-1.1.0.tar.gz`, and upload that stable artifact with final notes.

## AppInspect exit-code handling

The workflow preserves `dist/appinspect-<version>.exit-code` so the gate reports the native AppInspect status rather than GNU Make's generic recipe-failure status 2.
