# Publishing 1.0.1

## Local preflight

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-build.txt
./scripts/build_release.sh 1.0.1
```

Review `dist/appinspect-1.0.1.json`. Do not publish while any failure remains.

## GitHub release

Commit the release files, push `main`, then create and push the tag:

```bash
git add .
git commit -m "release: REST Profiler 1.0.1"
git push origin main
git tag -a v1.0.1 -m "REST Profiler for Splunk 1.0.1"
git push origin v1.0.1
```

The workflow creates the GitHub Releases entry and uploads:

- `rest_profiler-1.0.1.tar.gz`
- `SHA256SUMS.txt`
- `appinspect-1.0.1.json`

## Splunkbase release

Upload the exact `rest_profiler-1.0.1.tar.gz` asset produced by the workflow as a new Splunkbase release. Use the text in `release-notes/1.0.1.md`. Splunkbase then runs the current AppInspect cloud evaluation automatically.
