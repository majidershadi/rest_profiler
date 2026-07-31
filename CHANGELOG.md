# Changelog

## [1.0.1] - 2026-07-31

- Preserve and report the native AppInspect exit code instead of GNU Make's generic exit code 2.

### Fixed

- Regenerated the UCC-managed static HTML bootstrap with UCC 6.5.3; AppInspect 4.3.0 still path-flags the generated loader as a future failure.
- Restored source build inputs excluded by generic `.gitignore` rules.

### Build

- Updated Splunk UCC Framework to 6.5.3.
- Updated the packaged `splunktaucclib` range to `>=8.2.0,<9` to satisfy the UCC build-time dependency check.
- Updated Splunk AppInspect to 4.3.0.
- Added a Makefile release interface and tag-driven automation that preserves AppInspect diagnostics and publishes only after a passing gate.

## [1.0.0] - 2026-06-27

- First stable release.
