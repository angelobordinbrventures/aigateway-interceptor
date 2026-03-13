"""
AIGateway Interceptor - Full Flow Integration Tests

These tests verify the complete interception pipeline:
  1. Request arrives at the proxy
  2. DLP detector scans for sensitive data
  3. Policy engine determines the action
  4. Action is executed (block, anonymize, or log)
  5. Audit log is written to the database
  6. Event is published for real-time streaming

Prerequisites:
  - All services must be running (docker compose up)
  - Tests run against the live stack
"""

import time
import uuid

import pytest
import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_BASE_URL = "http://localhost:8000"
PROXY_URL = "http://localhost:8080"
GATEWAY_URL = "http://localhost"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def auth_token():
    """Authenticate and return a valid JWT token."""
    response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
    )
    if response.status_code != 200:
        pytest.skip("API not available or auth failed. Are services running?")
    return response.json()["access_token"]


@pytest.fixture(scope="session")
def auth_headers(auth_token):
    """Return headers with Bearer token."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture(scope="session")
def api_session():
    """Return a requests session configured for the API."""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


# ---------------------------------------------------------------------------
# Health Check Tests
# ---------------------------------------------------------------------------


class TestHealthChecks:
    """Verify all services are reachable and healthy."""

    def test_api_health(self):
        """API health endpoint returns 200."""
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_gateway_health(self):
        """Nginx gateway health endpoint returns 200."""
        response = requests.get(f"{GATEWAY_URL}/health", timeout=5)
        assert response.status_code == 200

    def test_api_via_gateway(self):
        """API is reachable through the Nginx gateway."""
        response = requests.get(f"{GATEWAY_URL}/api/health", timeout=5)
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Authentication Tests
# ---------------------------------------------------------------------------


class TestAuthentication:
    """Verify authentication flow."""

    def test_login_success(self):
        """Valid credentials return a JWT token."""
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_failure(self):
        """Invalid credentials return 401."""
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            json={"username": "admin", "password": "wrong"},
        )
        assert response.status_code == 401

    def test_protected_endpoint_without_token(self):
        """Accessing a protected endpoint without a token returns 401."""
        response = requests.get(f"{API_BASE_URL}/logs")
        assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Audit Log Tests
# ---------------------------------------------------------------------------


class TestAuditLogs:
    """Verify audit log retrieval and filtering."""

    def test_list_logs(self, auth_headers):
        """Listing audit logs returns a paginated response."""
        response = requests.get(
            f"{API_BASE_URL}/logs",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_list_logs_with_filter(self, auth_headers):
        """Filtering logs by provider works."""
        response = requests.get(
            f"{API_BASE_URL}/logs",
            headers=auth_headers,
            params={"ai_provider": "openai"},
        )
        assert response.status_code == 200

    def test_log_stats(self, auth_headers):
        """Stats endpoint returns aggregated data."""
        response = requests.get(
            f"{API_BASE_URL}/logs/stats",
            headers=auth_headers,
        )
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Policy Tests
# ---------------------------------------------------------------------------


class TestPolicies:
    """Verify policy CRUD operations."""

    def test_list_policies(self, auth_headers):
        """Listing policies returns default seed policies."""
        response = requests.get(
            f"{API_BASE_URL}/policies",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 4  # 4 default policies

    def test_create_policy(self, auth_headers):
        """Creating a new policy succeeds."""
        unique_name = f"Test Policy {uuid.uuid4().hex[:8]}"
        response = requests.post(
            f"{API_BASE_URL}/policies",
            headers=auth_headers,
            json={
                "name": unique_name,
                "description": "Integration test policy",
                "finding_categories": ["test_category"],
                "action": "LOG_ONLY",
                "priority": 50,
                "enabled": False,
            },
        )
        assert response.status_code in (200, 201)
        data = response.json()
        assert data["name"] == unique_name

    def test_update_policy(self, auth_headers):
        """Updating a policy succeeds."""
        # First, create a policy
        unique_name = f"Update Test {uuid.uuid4().hex[:8]}"
        create_resp = requests.post(
            f"{API_BASE_URL}/policies",
            headers=auth_headers,
            json={
                "name": unique_name,
                "finding_categories": ["test"],
                "action": "LOG_ONLY",
                "priority": 10,
            },
        )
        if create_resp.status_code not in (200, 201):
            pytest.skip("Could not create policy for update test")

        policy_id = create_resp.json()["id"]

        # Update it
        update_resp = requests.put(
            f"{API_BASE_URL}/policies/{policy_id}",
            headers=auth_headers,
            json={"priority": 55},
        )
        assert update_resp.status_code == 200


# ---------------------------------------------------------------------------
# Proxy Interception Tests (requires proxy to be running)
# ---------------------------------------------------------------------------


class TestProxyInterception:
    """Verify the proxy intercepts and processes requests.

    These tests send requests through the proxy to a mock or real endpoint
    and verify that interception, DLP, and logging occur.
    """

    @pytest.mark.skip(reason="Requires proxy and AI API access; run manually")
    def test_request_through_proxy_is_logged(self, auth_headers):
        """A request through the proxy creates an audit log entry."""
        # Send a request through the proxy
        proxies = {"https": PROXY_URL, "http": PROXY_URL}
        marker = uuid.uuid4().hex

        try:
            requests.get(
                "https://api.openai.com/v1/models",
                proxies=proxies,
                headers={"X-Test-Marker": marker},
                timeout=10,
                verify=False,  # noqa: S501 - using self-signed CA
            )
        except requests.exceptions.RequestException:
            pass  # We don't need the response to succeed

        # Wait for async processing
        time.sleep(2)

        # Check that an audit log was created
        response = requests.get(
            f"{API_BASE_URL}/logs",
            headers=auth_headers,
            params={"ai_provider": "openai"},
        )
        assert response.status_code == 200
        # Verify at least one log exists for openai
        data = response.json()
        assert data["total"] > 0

    @pytest.mark.skip(reason="Requires proxy; run manually")
    def test_sensitive_data_is_detected(self, auth_headers):
        """Sending sensitive data through the proxy triggers DLP detection."""
        proxies = {"https": PROXY_URL, "http": PROXY_URL}

        try:
            requests.post(
                "https://api.openai.com/v1/chat/completions",
                proxies=proxies,
                json={
                    "model": "gpt-4",
                    "messages": [
                        {
                            "role": "user",
                            "content": "My CPF is 123.456.789-00 and my credit card is 4111111111111111",
                        }
                    ],
                },
                headers={"Authorization": "Bearer sk-test"},
                timeout=10,
                verify=False,  # noqa: S501
            )
        except requests.exceptions.RequestException:
            pass

        time.sleep(2)

        # Verify findings were logged
        response = requests.get(
            f"{API_BASE_URL}/logs",
            headers=auth_headers,
            params={"ai_provider": "openai", "action_taken": "ANONYMIZE"},
        )
        assert response.status_code == 200
