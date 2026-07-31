#!/usr/bin/env python3
"""Release integrity checks for REST Profiler."""

from __future__ import annotations

import argparse
import configparser
import json
import py_compile
import re
import sys
import tarfile
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

APP = "rest_profiler"
EXPECTED_UCC = "6.5.3"


def fail(message: str) -> None:
    raise RuntimeError(message)


def app_root_from(path: Path, temp: Path) -> Path:
    if path.is_dir():
        if path.name == APP:
            return path
        candidate = path / APP
        if candidate.is_dir():
            return candidate
        fail(f"Could not find {APP}/ under {path}")
    if not tarfile.is_tarfile(path):
        fail(f"Not a directory or tar archive: {path}")
    with tarfile.open(path, "r:*") as archive:
        members = archive.getmembers()
        for member in members:
            parts = Path(member.name).parts
            if member.name.startswith("/") or ".." in parts:
                fail(f"Unsafe archive member: {member.name}")
        roots = {Path(m.name).parts[0] for m in members if Path(m.name).parts}
        if roots != {APP}:
            fail(f"Archive must contain exactly one root named {APP}: {sorted(roots)}")
        archive.extractall(temp, filter="data")
    return temp / APP


def conf_version(root: Path) -> tuple[str, str, str]:
    parser = configparser.RawConfigParser(strict=False)
    parser.optionxform = str
    parser.read(root / "default" / "app.conf", encoding="utf-8")
    return (
        parser.get("launcher", "version"),
        parser.get("id", "version"),
        parser.get("install", "build"),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("version")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="rest-profiler-verify-") as tmp:
        root = app_root_from(args.path.resolve(), Path(tmp))
        expected = args.version

        launcher, app_id, build = conf_version(root)
        if launcher != expected or app_id != expected:
            fail(f"app.conf versions differ: launcher={launcher}, id={app_id}, expected={expected}")
        if not re.fullmatch(r"\d{10}", build):
            fail(f"app.conf build must be a ten-digit timestamp: {build}")

        manifest = json.loads((root / "app.manifest").read_text(encoding="utf-8"))
        if manifest["info"]["id"]["name"] != APP:
            fail("app.manifest app ID mismatch")
        if manifest["info"]["id"]["version"] != expected:
            fail("app.manifest version mismatch")

        version_lines = (root / "VERSION").read_text(encoding="utf-8").splitlines()
        if version_lines != [expected, expected]:
            fail(f"VERSION content mismatch: {version_lines!r}")

        gc = json.loads((root / "appserver/static/js/build/globalConfig.json").read_text(encoding="utf-8"))
        meta = gc["meta"]
        if meta.get("version") != expected:
            fail("generated globalConfig version mismatch")
        if meta.get("_uccVersion") != EXPECTED_UCC:
            fail(f"generated UCC version mismatch: {meta.get('_uccVersion')}")

        openapi = json.loads((root / "appserver/static/openapi.json").read_text(encoding="utf-8"))
        if openapi["info"]["version"] != expected:
            fail("OpenAPI version mismatch")

        template_dir = root / "appserver" / "templates"
        template_files = sorted(p.name for p in template_dir.iterdir() if p.is_file())
        if template_files != ["base.html"]:
            fail(f"Unexpected template files: {template_files}")
        base = (template_dir / "base.html").read_text(encoding="utf-8")
        forbidden = ("<%", "${", "cherrypy", "make_url(", "window.$C", "__APP_NAME__")
        present = [x for x in forbidden if x in base]
        required = (
            "../../config?autoload=1",
            f"../../static/@{build}/js/i18n.js",
            f"../../static/@{build}/app/{APP}/js/build/entry_page.js",
        )
        missing = [x for x in required if x not in base]
        if present or missing:
            fail(f"base.html is not the managed static bootstrap; forbidden={present}, missing={missing}")

        forbidden_paths = []
        for path in root.rglob("*"):
            if path.is_symlink():
                forbidden_paths.append(str(path.relative_to(root)) + " (symlink)")
            if path.is_file() and (path.suffix in {".pyc", ".pyo", ".so"} or path.name in {".DS_Store", "Thumbs.db"}):
                forbidden_paths.append(str(path.relative_to(root)))
        if forbidden_paths:
            fail(f"Forbidden packaged files: {forbidden_paths}")

        for path in root.rglob("*.json"):
            json.loads(path.read_text(encoding="utf-8"))
        for path in root.rglob("*.xml"):
            ET.parse(path)
        for path in (root / "bin").glob("*.py"):
            py_compile.compile(str(path), doraise=True, cfile=str(Path(tmp) / (path.name + ".pyc")))

        print(f"PASS: {APP} {expected}")
        print(f"  build: {build}")
        print(f"  UCC: {EXPECTED_UCC}")
        print("  managed base.html: static and build-stamped")
        print("  JSON/XML/Python syntax: valid")
        print("  forbidden package artifacts: none")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
