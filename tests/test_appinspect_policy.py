import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "evaluate_appinspect.py"
SPEC = importlib.util.spec_from_file_location("evaluate_appinspect", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def report_with(*checks):
    summary = {
        "error": sum(check["result"] == "error" for check in checks),
        "failure": sum(check["result"] == "failure" for check in checks),
        "future_failure": sum(
            check["result"] == "future_failure" for check in checks
        ),
    }
    return {"summary": summary, "reports": [{"groups": [{"checks": list(checks)}]}]}


class AppInspectPolicyTests(unittest.TestCase):
    def test_accepts_splunk_deferred_template_check(self):
        allowed, messages = MODULE.evaluate(
            report_with(
                {
                    "name": "check_for_custom_mako_templates",
                    "result": "future_failure",
                }
            )
        )
        self.assertTrue(allowed)
        self.assertIn(
            "deferred warning: check_for_custom_mako_templates", messages
        )

    def test_rejects_current_failure(self):
        allowed, messages = MODULE.evaluate(
            report_with({"name": "check_current_security_rule", "result": "failure"})
        )
        self.assertFalse(allowed)
        self.assertIn("failure: check_current_security_rule", messages)

    def test_rejects_unlisted_future_failure(self):
        allowed, messages = MODULE.evaluate(
            report_with({"name": "check_new_future_rule", "result": "future_failure"})
        )
        self.assertFalse(allowed)
        self.assertIn("future_failure: check_new_future_rule", messages)

    def test_rejects_empty_report(self):
        allowed, messages = MODULE.evaluate({"summary": {}, "reports": []})
        self.assertFalse(allowed)
        self.assertIn("report contains no application results", messages)


if __name__ == "__main__":
    unittest.main()
