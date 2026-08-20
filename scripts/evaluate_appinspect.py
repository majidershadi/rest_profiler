#!/usr/bin/env python3
"""Apply the documented Splunk AppInspect release policy to a JSON report."""

from __future__ import annotations

import json
import sys
from pathlib import Path


DEFERRED_WARNING_CHECKS = {
    "check_for_custom_mako_templates",
    "check_for_existence_of_python_code_block_in_mako_template",
    "check_cherrypy_controllers",
    "check_for_ucc_framework_version",
}


def evaluate(report: dict) -> tuple[bool, list[str]]:
    blocking: list[str] = []
    deferred: list[str] = []
    observed = {"error": 0, "failure": 0, "future_failure": 0}
    check_count = 0

    reports = report.get("reports", [])
    if not isinstance(reports, list) or not reports:
        return False, ["report contains no application results"]

    for app_report in reports:
        for group in app_report.get("groups", []):
            for check in group.get("checks", []):
                check_count += 1
                result = check.get("result")
                name = check.get("name", "<unnamed check>")
                if result in observed:
                    observed[result] += 1
                if result in {"error", "failure"}:
                    blocking.append(f"{result}: {name}")
                elif result == "future_failure":
                    if name in DEFERRED_WARNING_CHECKS:
                        deferred.append(name)
                    else:
                        blocking.append(f"future_failure: {name}")

    if not check_count:
        blocking.append("report contains no checks")

    summary = report.get("summary", {})
    for result, count in observed.items():
        if summary.get(result) != count:
            blocking.append(
                f"report summary mismatch for {result}: "
                f"summary={summary.get(result)!r}, observed={count}"
            )

    messages = [f"deferred warning: {name}" for name in sorted(set(deferred))]
    messages.extend(blocking)
    return not blocking, messages


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: evaluate_appinspect.py <appinspect-report.json>", file=sys.stderr)
        return 2

    path = Path(argv[1])
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"AppInspect policy gate could not read {path}: {error}", file=sys.stderr)
        return 2

    allowed, messages = evaluate(report)
    for message in messages:
        print(f"AppInspect policy: {message}")
    if not allowed:
        print("AppInspect policy gate failed.", file=sys.stderr)
        return 1

    print("AppInspect policy gate passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
