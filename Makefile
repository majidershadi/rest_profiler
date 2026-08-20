TA := rest_profiler
PYTHON ?= python3
VERSION ?= $(shell $(PYTHON) -c 'import json; print(json.load(open("globalConfig.json", encoding="utf-8"))["meta"]["version"])')
OUT := output/$(TA)
DIST := dist
ARCHIVE := $(DIST)/$(TA)-$(VERSION).tar.gz
APPINSPECT_REPORT := $(DIST)/appinspect-$(VERSION).json
APPINSPECT_STATUS := $(DIST)/appinspect-$(VERSION).exit-code
APPINSPECT_ARGS := --mode precert --included-tags cloud --included-tags self-service --data-format json --max-messages all --ci

.PHONY: all help preflight purge-bytecode clean build verify package appinspect appinspect-only release

all: package

help:
	@printf '%s\n' \
	  'REST Profiler release targets:' \
	  '  make preflight                 Validate tools and VERSION' \
	  '  make build VERSION=x.y.z       Generate output/rest_profiler with UCC' \
	  '  make verify VERSION=x.y.z      Verify the generated app' \
	  '  make package VERSION=x.y.z     Build, verify, package, and checksum' \
	  '  make appinspect VERSION=x.y.z  Package and run AppInspect' \
	  '  make release VERSION=x.y.z     Clean package plus AppInspect policy gate' \
	  '  make clean                     Remove generated release artifacts'

preflight:
	@$(PYTHON) -c 'import re, sys; v="$(VERSION)"; sys.exit(0 if re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", v) else "VERSION must be semantic x.y.z")'
	@command -v ucc-gen >/dev/null || { echo 'ucc-gen is not installed' >&2; exit 1; }
	@$(PYTHON) -c 'import json, sys; configured=json.load(open("globalConfig.json", encoding="utf-8"))["meta"]["version"]; expected="$(VERSION)"; sys.exit(0 if configured == expected else f"globalConfig.json version {configured} does not match VERSION {expected}")'

purge-bytecode:
	@find package scripts -type d -name __pycache__ -prune -exec rm -rf {} +
	@find package scripts -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete

clean: purge-bytecode
	rm -rf output dist
	rm -f $(TA)-*.tar.gz

build: preflight purge-bytecode
	rm -rf "$(OUT)"
	ucc-gen build --source package --ta-version "$(VERSION)" --overwrite
	$(PYTHON) scripts/verify_release.py "$(OUT)" "$(VERSION)"

verify:
	$(PYTHON) scripts/verify_release.py "$(OUT)" "$(VERSION)"

package: build
	mkdir -p "$(DIST)"
	rm -f "$(TA)-$(VERSION).tar.gz" "$(ARCHIVE)" "$(DIST)/SHA256SUMS.txt"
	ucc-gen package --path "$(OUT)"
	@test -f "$(TA)-$(VERSION).tar.gz" || { echo 'ucc-gen package did not create the expected archive' >&2; exit 1; }
	mv "$(TA)-$(VERSION).tar.gz" "$(ARCHIVE)"
	$(PYTHON) scripts/verify_release.py "$(ARCHIVE)" "$(VERSION)"
	cd "$(DIST)" && sha256sum "$(TA)-$(VERSION).tar.gz" > SHA256SUMS.txt
	@echo "Created $(ARCHIVE)"

appinspect-only:
	@command -v splunk-appinspect >/dev/null || { echo 'splunk-appinspect is not installed' >&2; exit 1; }
	@test -f "$(ARCHIVE)" || { echo 'Package is missing; run make package first' >&2; exit 1; }
	rm -f "$(APPINSPECT_REPORT)" "$(APPINSPECT_STATUS)"
	@set +e; \
	  splunk-appinspect inspect "$(ARCHIVE)" $(APPINSPECT_ARGS) --output-file "$(APPINSPECT_REPORT)"; \
	  code=$$?; \
	  printf '%s\n' "$$code" > "$(APPINSPECT_STATUS)"; \
	  exit "$$code"

appinspect: package
	$(MAKE) appinspect-only VERSION="$(VERSION)"

release:
	$(MAKE) clean
	$(MAKE) package VERSION="$(VERSION)"
	@set +e; \
	  $(MAKE) appinspect-only VERSION="$(VERSION)"; \
	  set -e; \
	  $(PYTHON) scripts/evaluate_appinspect.py "$(APPINSPECT_REPORT)"
	@echo "Release validation passed: $(ARCHIVE)"
