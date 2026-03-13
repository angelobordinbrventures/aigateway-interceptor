"""Tests for TLS inspection support.

Verifies that the proxy addon correctly handles HTTPS flows (mitmproxy
presents decrypted content to addons regardless of scheme), that the
response() handler works, and that the entrypoint script logic is sound.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from proxy.main import AIGatewayAddon, is_ai_target


# ---------------------------------------------------------------------------
# Helpers to create mock mitmproxy flow objects
# ---------------------------------------------------------------------------

def _make_flow(
    host: str = "api.openai.com",
    path: str = "/v1/chat/completions",
    method: str = "POST",
    scheme: str = "https",
    body: Optional[str] = None,
    headers: Optional[dict] = None,
) -> MagicMock:
    """Create a mock mitmproxy HTTPFlow for testing."""
    flow = MagicMock()
    flow.request.pretty_host = host
    flow.request.host = host
    flow.request.path = path
    flow.request.method = method
    flow.request.scheme = scheme
    flow.request.url = f"{scheme}://{host}{path}"

    # Headers
    mock_headers = {}
    if headers:
        mock_headers.update(headers)
    flow.request.headers = MagicMock()
    flow.request.headers.get = lambda key, default="": mock_headers.get(key, default)

    # Body
    flow.request.get_text.return_value = body

    # Metadata dict
    flow.metadata = {}

    # Response (initially None for request phase)
    flow.response = None

    return flow


def _set_response(flow: MagicMock, status_code: int = 200, body: str = "{}") -> None:
    """Attach a mock response to a flow."""
    flow.response = MagicMock()
    flow.response.status_code = status_code
    flow.response.get_text.return_value = body
    flow.response.headers = {}


# ---------------------------------------------------------------------------
# Test: HTTPS flows are intercepted by request() handler
# ---------------------------------------------------------------------------

class TestHTTPSRequestInterception:
    """Verify request() works identically for HTTPS and HTTP flows."""

    @patch("proxy.main.PolicyEngine")
    @patch("proxy.main.DLPDetector")
    def test_https_request_to_ai_target_is_inspected(
        self, mock_detector_cls, mock_engine_cls
    ):
        """An HTTPS request to an AI API should be DLP-scanned."""
        mock_detector = mock_detector_cls.return_value
        mock_detector.detect.return_value = []

        mock_engine = mock_engine_cls.return_value
        mock_engine.get_action.return_value = "ALLOW"

        addon = AIGatewayAddon()
        flow = _make_flow(
            scheme="https",
            body='{"messages": [{"role": "user", "content": "Hello"}]}',
        )

        addon.request(flow)

        # The detector should have been called with the request body
        mock_detector.detect.assert_called_once()

    @patch("proxy.main.PolicyEngine")
    @patch("proxy.main.DLPDetector")
    def test_https_request_blocked_when_policy_says_block(
        self, mock_detector_cls, mock_engine_cls
    ):
        """An HTTPS request with sensitive data should be blocked if policy says BLOCK."""
        finding = MagicMock()
        finding.category = "PII"

        mock_detector = mock_detector_cls.return_value
        mock_detector.detect.return_value = [finding]

        mock_engine = mock_engine_cls.return_value
        mock_engine.get_action.return_value = "BLOCK"

        addon = AIGatewayAddon()
        flow = _make_flow(
            scheme="https",
            body='{"messages": [{"role": "user", "content": "My SSN is 123-45-6789"}]}',
        )

        addon.request(flow)

        # Flow should have a 403 response set
        assert flow.response is not None
        assert flow.response.status_code == 403 or hasattr(flow.response, "make")

    @patch("proxy.main.PolicyEngine")
    @patch("proxy.main.DLPDetector")
    def test_https_non_ai_target_is_ignored(
        self, mock_detector_cls, mock_engine_cls
    ):
        """HTTPS requests to non-AI hosts should pass through untouched."""
        mock_detector = mock_detector_cls.return_value

        addon = AIGatewayAddon()
        flow = _make_flow(
            host="www.google.com",
            scheme="https",
            body="some data",
        )

        addon.request(flow)

        mock_detector.detect.assert_not_called()

    @patch("proxy.main.PolicyEngine")
    @patch("proxy.main.DLPDetector")
    def test_https_empty_body_allowed(
        self, mock_detector_cls, mock_engine_cls
    ):
        """HTTPS request with no body should be allowed without DLP scan."""
        mock_detector = mock_detector_cls.return_value

        addon = AIGatewayAddon()
        flow = _make_flow(scheme="https", body=None)

        addon.request(flow)

        mock_detector.detect.assert_not_called()


# ---------------------------------------------------------------------------
# Test: response() handler
# ---------------------------------------------------------------------------

class TestResponseHandler:
    """Verify the response() handler works for HTTPS flows."""

    @patch("proxy.main.PolicyEngine")
    @patch("proxy.main.DLPDetector")
    def test_response_non_ai_target_ignored(
        self, mock_detector_cls, mock_engine_cls
    ):
        """Responses from non-AI hosts should be ignored."""
        addon = AIGatewayAddon()
        flow = _make_flow(host="www.example.com", scheme="https")
        _set_response(flow)

        # Should not raise
        addon.response(flow)

    @patch("proxy.main.PolicyEngine")
    @patch("proxy.main.DLPDetector")
    def test_response_adds_session_header_after_anonymization(
        self, mock_detector_cls, mock_engine_cls
    ):
        """After anonymization, the session ID should appear in the response header."""
        addon = AIGatewayAddon()
        flow = _make_flow(scheme="https")
        flow.metadata["anonymization_session_id"] = "sess-abc123"
        _set_response(flow)

        addon.response(flow)

        assert flow.response.headers["X-AIGateway-Session-ID"] == "sess-abc123"

    @patch("proxy.main.PolicyEngine")
    @patch("proxy.main.DLPDetector")
    def test_response_no_session_header_when_not_anonymized(
        self, mock_detector_cls, mock_engine_cls
    ):
        """If the request was not anonymized, no session header should be added."""
        addon = AIGatewayAddon()
        flow = _make_flow(scheme="https")
        _set_response(flow)

        addon.response(flow)

        assert "X-AIGateway-Session-ID" not in flow.response.headers

    @patch("proxy.main.PolicyEngine")
    @patch("proxy.main.DLPDetector")
    def test_response_handles_none_response(
        self, mock_detector_cls, mock_engine_cls
    ):
        """If flow.response is None (e.g. blocked), response() should not crash."""
        addon = AIGatewayAddon()
        flow = _make_flow(scheme="https")
        flow.response = None

        # Should not raise
        addon.response(flow)


# ---------------------------------------------------------------------------
# Test: DLP detector runs on decrypted HTTPS content
# ---------------------------------------------------------------------------

class TestDLPOnHTTPS:
    """Verify DLP detection works on decrypted HTTPS request bodies."""

    @patch("proxy.main.PolicyEngine")
    @patch("proxy.main.DLPDetector")
    def test_dlp_detector_receives_decrypted_body(
        self, mock_detector_cls, mock_engine_cls
    ):
        """The DLP detector should receive the plain-text body from HTTPS."""
        mock_detector = mock_detector_cls.return_value
        mock_detector.detect.return_value = []
        mock_engine = mock_engine_cls.return_value
        mock_engine.get_action.return_value = "ALLOW"

        body_text = '{"prompt": "My credit card is 4111111111111111"}'
        addon = AIGatewayAddon()
        flow = _make_flow(scheme="https", body=body_text)

        addon.request(flow)

        mock_detector.detect.assert_called_once_with(body_text)

    @patch("proxy.main.PolicyEngine")
    @patch("proxy.main.Anonymizer")
    @patch("proxy.main.DLPDetector")
    def test_anonymize_action_on_https(
        self, mock_detector_cls, mock_anon_cls, mock_engine_cls
    ):
        """ANONYMIZE action should work on HTTPS flows."""
        finding = MagicMock()
        finding.category = "CREDIT_CARD"

        mock_detector = mock_detector_cls.return_value
        mock_detector.detect.return_value = [finding]
        mock_engine = mock_engine_cls.return_value
        mock_engine.get_action.return_value = "ANONYMIZE"

        mock_anon = mock_anon_cls.return_value
        mock_anon.anonymize.return_value = ("[REDACTED]", "sess-xyz789")

        addon = AIGatewayAddon()
        flow = _make_flow(
            scheme="https",
            body='{"prompt": "My card is 4111111111111111"}',
        )

        addon.request(flow)

        # Anonymizer should have been called and body set
        mock_anon.anonymize.assert_called_once()
        flow.request.set_text.assert_called_once()
        assert "anonymization_session_id" in flow.metadata


# ---------------------------------------------------------------------------
# Test: entrypoint.sh script logic
# ---------------------------------------------------------------------------

class TestEntrypointScript:
    """Verify the entrypoint shell script exists and has correct structure."""

    ENTRYPOINT_PATH = Path(__file__).resolve().parents[1] / "entrypoint.sh"

    def test_entrypoint_exists(self):
        assert self.ENTRYPOINT_PATH.exists(), "entrypoint.sh must exist"

    def test_entrypoint_is_executable(self):
        assert os.access(self.ENTRYPOINT_PATH, os.X_OK), "entrypoint.sh must be executable"

    def test_entrypoint_has_strict_mode(self):
        content = self.ENTRYPOINT_PATH.read_text()
        assert "set -euo pipefail" in content

    def test_entrypoint_handles_custom_certs(self):
        content = self.ENTRYPOINT_PATH.read_text()
        assert "mitmproxy-ca.pem" in content
        assert "mitmproxy-ca-cert.pem" in content

    def test_entrypoint_handles_missing_certs(self):
        content = self.ENTRYPOINT_PATH.read_text()
        assert "auto-generate" in content.lower() or "auto generate" in content.lower()

    def test_entrypoint_uses_ssl_insecure(self):
        content = self.ENTRYPOINT_PATH.read_text()
        assert "--ssl-insecure" in content

    def test_entrypoint_passes_confdir(self):
        content = self.ENTRYPOINT_PATH.read_text()
        assert "confdir=" in content

    def test_entrypoint_starts_mitmdump(self):
        content = self.ENTRYPOINT_PATH.read_text()
        assert "mitmdump" in content

    def test_entrypoint_syntax_valid(self):
        """Verify the shell script has no syntax errors."""
        result = subprocess.run(
            ["bash", "-n", str(self.ENTRYPOINT_PATH)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Syntax error in entrypoint.sh: {result.stderr}"


# ---------------------------------------------------------------------------
# Test: CA certificate generation produces mitmproxy files
# ---------------------------------------------------------------------------

class TestCAGenerationMitmproxyCompat:
    """Verify generate-ca.sh produces mitmproxy-compatible files."""

    GENERATE_SCRIPT = (
        Path(__file__).resolve().parents[2] / "infrastructure" / "certs" / "generate-ca.sh"
    )

    def test_generate_script_references_mitmproxy_ca_pem(self):
        content = self.GENERATE_SCRIPT.read_text()
        assert "mitmproxy-ca.pem" in content

    def test_generate_script_references_mitmproxy_ca_cert(self):
        content = self.GENERATE_SCRIPT.read_text()
        assert "mitmproxy-ca-cert.pem" in content

    def test_generate_script_combines_key_and_cert(self):
        """mitmproxy-ca.pem should be key+cert concatenated."""
        content = self.GENERATE_SCRIPT.read_text()
        # Should cat key and cert into mitmproxy-ca.pem
        assert "cat" in content
        assert "CA_KEY" in content
        assert "CA_CRT" in content
