"""
additional_packaging.py

UCC build hooks:
  1. Add the custom Search view to the generated navigation.
  2. Reject a legacy or unrendered UCC base.html before packaging.
  3. Overwrite the auto-generated alert-action HTML with markup that is valid for
     Splunk 10's alert-action renderer (splunk-control-group / splunk-search-dropdown
     / splunk-radio-input / splunk-text-input). The generated HTML was being flagged
     as "Malformed alert action HTML", which also prevented the parameters from being
     saved/passed to the alert script.

Both run after UCC has generated the output. cleanup_output_files() gets the exact
output path; additional_packaging() repeats the work against the default output
location in case generation happens after cleanup in this UCC version.
"""

import os
import shutil

VIEW_NAME = "rest_profiler_search"
ALERT_NAME = "rest_profiler_send_alert"
# Leftover files from the `ucc-gen init` demo-input scaffold; the add-on defines
# no modular inputs, so these must not ship.
DEMO_INPUT_FILES = (
    os.path.join("bin", "rest_profiler_helper.py"),
    os.path.join("bin", "rest_profiler.py"),
    os.path.join("default", "inputs.conf"),
    os.path.join("README", "inputs.conf.spec"),
)

ALERT_HTML = """<form class="form form-horizontal form-complex">
  <splunk-control-group label="Profile" help="Select the saved REST profile to execute when this alert fires.">
    <splunk-search-dropdown
      name="action.rest_profiler_send_alert.param.profile"
      search="| rest /servicesNS/nobody/rest_profiler/rest_profiler_profile splunk_server=local count=0 | dedup title | sort title | table title"
      value-field="title"
      label-field="title"
      earliest="-1m"
      latest="now">
    </splunk-search-dropdown>
  </splunk-control-group>
  <splunk-control-group label="Index the response as an event">
    <splunk-radio-input name="action.rest_profiler_send_alert.param.store_response" value="1">
      <option value="1">Yes</option>
      <option value="0">No</option>
    </splunk-radio-input>
  </splunk-control-group>
  <splunk-control-group label="Result index" help="Index to write the response event into when storing is enabled.">
    <splunk-text-input name="action.rest_profiler_send_alert.param.result_index" value="main"></splunk-text-input>
  </splunk-control-group>
</form>
"""


def _patch_nav(nav_path):
    if not os.path.isfile(nav_path):
        return
    with open(nav_path, "r", encoding="utf-8") as handle:
        content = handle.read()
    if VIEW_NAME in content or "</nav>" not in content:
        return
    entry = '  <view name="{name}" />\n'.format(name=VIEW_NAME)
    with open(nav_path, "w", encoding="utf-8") as handle:
        handle.write(content.replace("</nav>", entry + "</nav>", 1))


def _write_alert_html(alert_html_path):
    parent = os.path.dirname(alert_html_path)
    if not os.path.isdir(parent):
        return
    with open(alert_html_path, "w", encoding="utf-8") as handle:
        handle.write(ALERT_HTML)


def _remove_demo_input(base_dir, ta_name):
    for rel in DEMO_INPUT_FILES:
        path = os.path.join(base_dir, ta_name, rel)
        if os.path.isfile(path):
            os.remove(path)


def _scrub_arch_binaries(base_dir, ta_name):
    """Remove x86_64-only compiled modules from lib/.

    The add-on's dependency set is pure Python; any *-x86_64-linux-gnu.so that
    sneaks in (e.g. a binary wheel selected by the build host's pip) fails
    Splunk AppInspect AArch64 certification and cannot load under the Splunk
    runtime. A compiled module is removed only when its pure-Python fallback
    (same module name with a .py extension) exists next to it; mypyc shim
    libraries are removed once no compiled module depends on them.
    """
    lib_dir = os.path.join(base_dir, ta_name, "lib")
    if not os.path.isdir(lib_dir):
        return
    suffix = "-x86_64-linux-gnu.so"
    shims = []
    remaining = 0
    for root, _dirs, files in os.walk(lib_dir):
        for name in files:
            if not name.endswith(suffix):
                continue
            path = os.path.join(root, name)
            if "__mypyc" in name:
                shims.append(path)
                continue
            module_stem = name.split(".", 1)[0]
            fallback = os.path.join(root, module_stem + ".py")
            if os.path.isfile(fallback):
                os.remove(path)
                print("additional_packaging: removed %s (pure-Python fallback kept)" % path)
            else:
                remaining += 1
                print("additional_packaging: WARNING kept %s (no .py fallback found)" % path)
    if remaining == 0:
        for path in shims:
            os.remove(path)
            print("additional_packaging: removed orphaned mypyc shim %s" % path)


def _remove_unused_sdk_assistant(base_dir, ta_name):
    """Exclude the optional Splunk SDK assistant package from the app bundle.

    REST Profiler does not import this optional SDK subtree. Keeping it would
    increase the release size and expose unrelated third-party integrations.
    """
    path = os.path.join(base_dir, ta_name, "lib", "splunklib", "ai")
    if os.path.isdir(path):
        shutil.rmtree(path)
        print("additional_packaging: removed unused optional SDK assistant package")


def _neutralize_generated_assistant_labels(base_dir, ta_name):
    """Use neutral wording for optional controls embedded in UCC bundles."""
    build_dir = os.path.join(
        base_dir, ta_name, "appserver", "static", "js", "build"
    )
    if not os.path.isdir(build_dir):
        return
    replacements = (
        ("Dashboard AI Assistant", "Dashboard Assistant"),
        ("AI Assistant", "Assistant"),
        ("Ask AI", "Ask Assistant"),
    )
    for name in os.listdir(build_dir):
        if not name.endswith(".js"):
            continue
        path = os.path.join(build_dir, name)
        with open(path, "r", encoding="utf-8") as handle:
            content = handle.read()
        updated = content
        for old, new in replacements:
            updated = updated.replace(old, new)
        if updated != content:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(updated)
            print("additional_packaging: neutralized generated assistant labels in %s" % path)


def _ensure_key_in_stanza(path, stanza, key, value):
    """Idempotently insert `key = value` directly under [stanza] in a .conf."""
    if not os.path.isfile(path):
        return
    with open(path, "r", encoding="utf-8") as handle:
        lines = handle.readlines()
    header = "[%s]" % stanza
    out = []
    in_target = False
    present = False
    insert_at = None
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("["):
            in_target = stripped == header
            if in_target:
                insert_at = idx + 1
        elif in_target and stripped.split("=", 1)[0].strip() == key:
            present = True
    if present or insert_at is None:
        return
    out = lines[:insert_at] + ["%s = %s\n" % (key, value)] + lines[insert_at:]
    with open(path, "w", encoding="utf-8") as handle:
        handle.writelines(out)



def _validate_managed_base_html(base_dir, ta_name):
    """Fail the build if UCC emitted a legacy/custom Mako bootstrap.

    Splunk Cloud vetting rejects custom Mako templates. UCC 6.5.1+ renders its
    managed bootstrap as static HTML and embeds the build timestamp into static
    asset URLs. Keeping this assertion in the release path prevents a stale UCC
    output directory from being packaged again.
    """
    path = os.path.join(base_dir, ta_name, "appserver", "templates", "base.html")
    if not os.path.isfile(path):
        raise RuntimeError("UCC-managed appserver/templates/base.html is missing")
    with open(path, "r", encoding="utf-8") as handle:
        content = handle.read()
    forbidden = ("<%", "${", "cherrypy", "make_url(", "window.$C", "__APP_NAME__")
    found = [marker for marker in forbidden if marker in content]
    required = (
        "../../config?autoload=1",
        "../../static/@",
        "/app/%s/js/build/entry_page.js" % ta_name,
    )
    missing = [marker for marker in required if marker not in content]
    if found or missing:
        raise RuntimeError(
            "Unsupported UCC base.html; forbidden=%r missing=%r. "
            "Build from a clean output directory with the pinned UCC version."
            % (found, missing)
        )
    template_dir = os.path.dirname(path)
    unexpected = sorted(
        name for name in os.listdir(template_dir)
        if os.path.isfile(os.path.join(template_dir, name)) and name != "base.html"
    )
    if unexpected:
        raise RuntimeError("Unexpected appserver/templates files: %r" % unexpected)

def _patch_python_required(base_dir, ta_name):
    """Declare python.required = 3.13 on every Python-backed stanza.

    Splunk 10.2 deprecates python.version in favor of python.required
    (AppInspect: check_*_python_required). UCC 6.4 predates the attribute and
    cannot generate it, and shipping these .conf files in the source package
    would disable their generation entirely, so the post-build hook is the
    supported place to add it. python.version is kept for Splunk releases
    before 10.2. The add-on's Python code and bundled libraries are pure
    Python and compatible with both runtimes (3.9 and 3.13).
    """
    default_dir = os.path.join(base_dir, ta_name, "default")
    _ensure_key_in_stanza(
        os.path.join(default_dir, "alert_actions.conf"),
        ALERT_NAME, "python.required", "3.13",
    )
    _ensure_key_in_stanza(
        os.path.join(default_dir, "commands.conf"),
        "restprofilersend", "python.required", "3.13",
    )
    for stanza in ("admin_external:rest_profiler_profile",
                   "admin_external:rest_profiler_settings"):
        _ensure_key_in_stanza(
            os.path.join(default_dir, "restmap.conf"),
            stanza, "python.required", "3.13",
        )


def _apply(base_dir, ta_name):
    _patch_nav(
        os.path.join(base_dir, ta_name, "default", "data", "ui", "nav", "default.xml")
    )
    _write_alert_html(
        os.path.join(
            base_dir, ta_name, "default", "data", "ui", "alerts", ALERT_NAME + ".html"
        )
    )
    _remove_demo_input(base_dir, ta_name)
    _validate_managed_base_html(base_dir, ta_name)
    _scrub_arch_binaries(base_dir, ta_name)
    _remove_unused_sdk_assistant(base_dir, ta_name)
    _neutralize_generated_assistant_labels(base_dir, ta_name)
    _patch_python_required(base_dir, ta_name)


def cleanup_output_files(output_path, ta_name):
    _apply(output_path, ta_name)


def additional_packaging(ta_name=None):
    if ta_name:
        _apply("output", ta_name)
