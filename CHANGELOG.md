# Changelog

## [1.1.0] - 2026-08-20

### Added

- Encrypt complete saved request bodies through UCC and Splunk secure storage.
- Support `§secret§` markers for masking selected request-body fragments in
  previews while sending their original values without the delimiters.
- Support `§§` for a literal section sign and safely reject unmatched markers.

### Security

- Mask custom token headers, `Authorization`, and `Proxy-Authorization` in
  preview and returned request metadata.
- Keep complete body content encrypted at rest, whether or not fragments use
  preview-masking markers.

### Release

- Promote the validated 1.1.0 release candidate to stable.
- Apply Splunk's deferred-enforcement policy only to its four named
  Mako/CherryPy/UCC checks; all other AppInspect failures remain blocking.

## [1.1.0-rc.1] - 2026-08-14

### Added

- Encrypt complete saved request bodies through UCC and Splunk secure storage.
- Support `§secret§` markers that mask selected body fragments in previews and
  are removed immediately before live transmission.
- Support `§§` for a literal section sign and reject unmatched markers without
  echoing request content.

### Security

- Mask configured custom token headers, `Authorization`, and
  `Proxy-Authorization` in returned request metadata.
- Add unit and package-verifier gates for body encryption and masking behavior.

### Release

- Accept `vX.Y.Z-rc.N` tags and create GitHub prereleases while keeping the
  packaged Splunk app version at `X.Y.Z`.

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
