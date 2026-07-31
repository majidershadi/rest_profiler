#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:-}"
TARGET="${2:-release}"

if [[ -z "$VERSION" || ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "usage: $0 <major.minor.patch> [package|appinspect|release]" >&2
  exit 2
fi

case "$TARGET" in
  package|appinspect|release) ;;
  *)
    echo "unsupported target: $TARGET" >&2
    exit 2
    ;;
esac

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec make -C "$ROOT" "$TARGET" VERSION="$VERSION"
