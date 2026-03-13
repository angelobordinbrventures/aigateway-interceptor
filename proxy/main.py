"""Main mitmproxy addon for the AIGateway Interceptor.

Intercepts HTTP/HTTPS traffic to AI API providers, applies DLP detection
and policy-based actions (ALLOW, BLOCK, ANONYMIZE, LOG_ONLY, ALERT).
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Optional

from mitmproxy import http

from proxy.dlp.anonymizer import Anonymizer
from proxy.dlp.detector import DLPDetector
from proxy.policies.engine import PolicyEngine

logger = logging.getLogger(__name__)

# AI API target hosts
AI_API_TARGETS: set[str] = {
    "api.anthropic.com",
    "api.openai.com",
    "generativelanguage.googleapis.com",
    "api.groq.com",
    "api.x.ai",
    "api.deepseek.com",
    "api.mistral.ai",
    "api.cohere.ai",
    "openrouter.ai",
}


def is_ai_target(host: str) -> bool:
    """Check if the given host is a known AI API target.

    Args:
        host: The hostname to check.

    Returns:
        True if the host matches a known AI API target.
    """
    return host in AI_API_TARGETS


class AIGatewayAddon:
    """mitmproxy addon that intercepts and inspects AI API traffic."""

    def __init__(self) -> None:
        self._detector = DLPDetector()
        self._anonymizer = Anonymizer()
        self._policy_engine = PolicyEngine(
            api_url=os.environ.get("AIGATEWAY_API_URL"),
        )
        self._api_backend_url = os.environ.get(
            "AIGATEWAY_API_URL", "http://localhost:3000"
        )
        logger.info("AIGateway Interceptor addon initialized")

    def request(self, flow: http.HTTPFlow) -> None:
        """Process intercepted HTTP requests.

        Called by mitmproxy for each request passing through the proxy.
        """
        host = flow.request.pretty_host

        if not is_ai_target(host):
            return

        body = flow.request.get_text()
        if not body:
            self._log_request(flow, [], "ALLOW")
            return

        try:
            findings = self._detector.detect(body)
            action = self._policy_engine.get_action(
                host=host,
                findings=findings,
                user=self._extract_user(flow),
            )

            if action == "BLOCK":
                self._block_request(flow, findings)
            elif action == "ANONYMIZE":
                self._anonymize_request(flow, findings)
            elif action == "ALERT":
                self._alert(flow, findings)
            # ALLOW and LOG_ONLY: let the request pass through

            self._log_request(flow, findings, action)

        except Exception as exc:
            logger.error(
                "Error processing request to %s: %s",
                host,
                exc,
                exc_info=True,
            )
            # On error, allow the request to pass but log the failure
            self._log_request(flow, [], "ERROR", error=str(exc))

    def _block_request(
        self, flow: http.HTTPFlow, findings: list
    ) -> None:
        """Block the request by returning a 403 response."""
        categories = list({f.category for f in findings})
        flow.response = http.Response.make(
            403,
            json.dumps(
                {
                    "error": "Request blocked by AIGateway DLP policy",
                    "categories_detected": categories,
                }
            ),
            {"Content-Type": "application/json"},
        )
        logger.warning(
            "BLOCKED request to %s - categories: %s",
            flow.request.pretty_host,
            categories,
        )

    def _anonymize_request(
        self, flow: http.HTTPFlow, findings: list
    ) -> None:
        """Anonymize sensitive data in the request body."""
        body = flow.request.get_text()
        if not body:
            return

        anonymized_text, session_id = self._anonymizer.anonymize(
            body, findings
        )
        flow.request.set_text(anonymized_text)

        # Store session_id in flow metadata for audit trail
        flow.metadata["anonymization_session_id"] = session_id

        logger.info(
            "ANONYMIZED request to %s - session: %s - %d findings",
            flow.request.pretty_host,
            session_id,
            len(findings),
        )

    def _alert(self, flow: http.HTTPFlow, findings: list) -> None:
        """Send an alert about detected findings but allow the request."""
        categories = list({f.category for f in findings})
        logger.warning(
            "ALERT: Sensitive data detected in request to %s - categories: %s",
            flow.request.pretty_host,
            categories,
        )

    def _extract_user(self, flow: http.HTTPFlow) -> Optional[str]:
        """Extract user identifier from request headers or auth."""
        # Check for custom header first
        user = flow.request.headers.get("X-AIGateway-User")
        if user:
            return user

        # Try to extract from Authorization header
        auth = flow.request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            # Return a truncated version of the token as user identifier
            token = auth[7:]
            if len(token) > 8:
                return f"bearer:{token[:8]}..."
        return None

    def _log_request(
        self,
        flow: http.HTTPFlow,
        findings: list,
        action: str,
        error: Optional[str] = None,
    ) -> None:
        """Log the request details to the API backend."""
        log_entry = {
            "timestamp": time.time(),
            "host": flow.request.pretty_host,
            "path": flow.request.path,
            "method": flow.request.method,
            "action": action,
            "findings_count": len(findings),
            "categories": list({f.category for f in findings}),
            "user": self._extract_user(flow),
        }

        if error:
            log_entry["error"] = error

        try:
            import requests as req_lib

            req_lib.post(
                f"{self._api_backend_url}/api/v1/logs",
                json=log_entry,
                timeout=2,
            )
        except Exception as exc:
            logger.debug("Could not send log to API backend: %s", exc)


addons = [AIGatewayAddon()]
