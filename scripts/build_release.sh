#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:-}"
if [[ -z "$VERSION" || ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "usage: $0 <major.minor.patch>" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

rm -rf output dist
mkdir -p dist

ucc-gen build --source package --ta-version "$VERSION" --overwrite
python scripts/verify_release.py output/rest_profiler "$VERSION"
ucc-gen package --path output/rest_profiler

ARCHIVE="$(find . -maxdepth 1 -type f -name 'rest_profiler-*.tar.gz' -printf '%f\n' | sort | tail -1)"
if [[ -z "$ARCHIVE" ]]; then
  echo "ucc-gen package did not create an archive" >&2
  exit 1
fi
EXPECTED="rest_profiler-${VERSION}.tar.gz"
if [[ "$ARCHIVE" != "$EXPECTED" ]]; then
  mv -- "$ARCHIVE" "$EXPECTED"
fi
mv -- "$EXPECTED" dist/
python scripts/verify_release.py "dist/$EXPECTED" "$VERSION"
(
  cd dist
  sha256sum "$EXPECTED" > SHA256SUMS.txt
)

# Run the official local checks used by this repository. Splunkbase performs
# its own current AppInspect evaluation after upload.
splunk-appinspect inspect "dist/$EXPECTED" --mode precert --included-tags cloud --included-tags self-service --data-format json --output-file "dist/appinspect-$VERSION.json" --max-messages all --ci

echo "Created dist/$EXPECTED"
