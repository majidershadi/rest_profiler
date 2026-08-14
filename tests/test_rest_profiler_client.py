"""Security-focused tests for request composition and secret masking."""

import sys
import types
import unittest
from pathlib import Path


# The client imports Splunk libraries at module load time. These tests exercise
# pure request composition, so small stubs keep them runnable in GitHub Actions
# before UCC installs the packaged Splunk runtime libraries.
solnlib = types.ModuleType("solnlib")
solnlib.conf_manager = types.SimpleNamespace()
solnlib.log = types.SimpleNamespace()
sys.modules.setdefault("solnlib", solnlib)

requests = types.ModuleType("requests")
requests_adapters = types.ModuleType("requests.adapters")


class HTTPAdapter:
    def __init__(self, *args, **kwargs):
        pass


requests_adapters.HTTPAdapter = HTTPAdapter
requests.adapters = requests_adapters
sys.modules.setdefault("requests", requests)
sys.modules.setdefault("requests.adapters", requests_adapters)

BIN = Path(__file__).resolve().parents[1] / "package" / "bin"
sys.path.insert(0, str(BIN))

import rest_profiler_client as client  # noqa: E402


class BodySecretTests(unittest.TestCase):
    def test_marked_values_are_masked_in_preview_and_revealed_for_send(self):
        body = '{"username":"§alice§","password":"§change-me§"}'
        self.assertEqual(
            client.render_body_secrets(body),
            '{"username":"********","password":"********"}',
        )
        self.assertEqual(
            client.render_body_secrets(body, reveal=True),
            '{"username":"alice","password":"change-me"}',
        )

    def test_double_marker_is_a_literal_section_sign(self):
        self.assertEqual(client.render_body_secrets("cost=10§§"), "cost=10§")
        self.assertEqual(
            client.render_body_secrets("§a§§b§", reveal=True), "a§b"
        )

    def test_unmatched_marker_fails_without_echoing_body(self):
        secret = "must-not-appear"
        with self.assertRaises(ValueError) as raised:
            client.render_body_secrets("prefix §" + secret)
        self.assertNotIn(secret, str(raised.exception))

    def test_compose_masks_body_but_live_request_strips_markers(self):
        profile = {
            "http_method": "POST",
            "uri": "https://example.invalid/login",
            "content_type": "application/json",
            "body": '{"password":"§secret§"}',
        }
        preview = client.compose(profile, reveal=False)
        live = client.compose(profile, reveal=True)
        self.assertEqual(preview["body"], '{"password":"********"}')
        self.assertEqual(live["body"], '{"password":"secret"}')

    def test_template_substitution_happens_after_marker_processing(self):
        profile = {
            "http_method": "POST",
            "uri": "https://example.invalid",
            "body": '{"account":"§alice§","value":"$value$"}',
            "send_results": "1",
            "result_format": "template",
        }
        composed = client.compose(profile, reveal=True, event={"value": "x§y"})
        self.assertEqual(composed["body"], '{"account":"alice","value":"x§y"}')


class HeaderMaskingTests(unittest.TestCase):
    def test_custom_token_header_is_masked_after_live_composition(self):
        profile = {
            "http_method": "POST",
            "uri": "https://example.invalid",
            "auth_type": "token",
            "token_header": "X-API-Key",
            "token_prefix": "Bearer",
            "token_value": "top-secret",
        }
        composed = client.compose(profile, reveal=True)
        self.assertEqual(composed["headers"]["X-API-Key"], "Bearer top-secret")
        self.assertEqual(client.compose_masked_headers(composed)["X-API-Key"], client.MASK)

    def test_manual_authorization_and_proxy_authorization_are_masked(self):
        composed = client.compose(
            {
                "http_method": "POST",
                "uri": "https://example.invalid",
                "headers": "Authorization: raw\nProxy-Authorization: proxy",
            },
            reveal=True,
        )
        safe = client.compose_masked_headers(composed)
        self.assertEqual(safe["Authorization"], client.MASK)
        self.assertEqual(safe["Proxy-Authorization"], client.MASK)


if __name__ == "__main__":
    unittest.main()
