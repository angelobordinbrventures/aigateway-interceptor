import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_create_policy(client: AsyncClient):
    response = await client.post(
        "/policies",
        json={
            "name": "Test Policy",
            "description": "A test policy",
            "ai_targets": ["openai", "anthropic"],
            "finding_categories": ["pii"],
            "action": "block",
            "priority": 5,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Policy"
    assert data["action"] == "block"
    assert data["enabled"] is True
    assert "id" in data


@pytest.mark.asyncio
async def test_list_policies(client: AsyncClient, sample_policy: dict):
    response = await client.get("/policies")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1


@pytest.mark.asyncio
async def test_get_policy(client: AsyncClient, sample_policy: dict):
    policy_id = sample_policy["id"]
    response = await client.get(f"/policies/{policy_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == policy_id
    assert data["name"] == sample_policy["name"]


@pytest.mark.asyncio
async def test_update_policy(client: AsyncClient, sample_policy: dict):
    policy_id = sample_policy["id"]
    response = await client.put(
        f"/policies/{policy_id}",
        json={"name": "Updated Policy Name", "priority": 99},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Policy Name"
    assert data["priority"] == 99


@pytest.mark.asyncio
async def test_delete_policy(client: AsyncClient, sample_policy: dict):
    policy_id = sample_policy["id"]
    response = await client.delete(f"/policies/{policy_id}")
    assert response.status_code == 204

    # Verify it is gone
    response = await client.get(f"/policies/{policy_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_toggle_policy(client: AsyncClient):
    # Create a fresh policy for this test
    create_resp = await client.post(
        "/policies",
        json={
            "name": "Toggle Me",
            "action": "block",
            "priority": 1,
        },
    )
    assert create_resp.status_code == 201
    policy = create_resp.json()
    assert policy["enabled"] is True

    # Toggle off
    response = await client.patch(f"/policies/{policy['id']}/toggle")
    assert response.status_code == 200
    assert response.json()["enabled"] is False

    # Toggle back on
    response = await client.patch(f"/policies/{policy['id']}/toggle")
    assert response.status_code == 200
    assert response.json()["enabled"] is True


@pytest.mark.asyncio
async def test_create_audit_log(client: AsyncClient):
    response = await client.post(
        "/logs",
        json={
            "user_identifier": "user1",
            "source_ip": "10.0.0.1",
            "ai_provider": "openai",
            "action_taken": "allowed",
            "findings": {"categories": [], "count": 0},
            "response_code": 200,
            "processing_time_ms": 5.2,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["ai_provider"] == "openai"
    assert data["action_taken"] == "allowed"
    assert "id" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_list_logs_with_filters(client: AsyncClient, sample_audit_log: dict):
    # No filters
    response = await client.get("/logs")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1

    # Filter by provider
    response = await client.get("/logs", params={"ai_provider": "openai"})
    assert response.status_code == 200
    data = response.json()
    assert all(item["ai_provider"] == "openai" for item in data["items"])

    # Filter by action
    response = await client.get("/logs", params={"action": "blocked"})
    assert response.status_code == 200
    data = response.json()
    assert all(item["action_taken"] == "blocked" for item in data["items"])

    # Filter that returns nothing
    response = await client.get("/logs", params={"ai_provider": "nonexistent"})
    assert response.status_code == 200
    assert response.json()["total"] == 0


@pytest.mark.asyncio
async def test_stats_overview(client: AsyncClient, sample_audit_log: dict):
    response = await client.get("/stats/overview")
    assert response.status_code == 200
    data = response.json()
    assert "total_requests" in data
    assert "blocked" in data
    assert "anonymized" in data
    assert "allowed" in data
    assert data["total_requests"] >= 1
    assert data["blocked"] >= 1


@pytest.mark.asyncio
async def test_create_user(client: AsyncClient):
    response = await client.post(
        "/users",
        json={
            "username": "testadmin",
            "email": "admin@test.com",
            "password": "securepassword123",
            "role": "admin",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testadmin"
    assert data["email"] == "admin@test.com"
    assert data["role"] == "admin"
    assert data["is_active"] is True
    assert "id" in data
    # Password should not be in the response
    assert "password" not in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_login_and_me(client: AsyncClient):
    # Create user
    await client.post(
        "/users",
        json={
            "username": "loginuser",
            "email": "login@test.com",
            "password": "securepassword123",
            "role": "viewer",
        },
    )

    # Login
    response = await client.post(
        "/auth/token",
        json={"username": "loginuser", "password": "securepassword123"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]

    # Get current user
    response = await client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["username"] == "loginuser"


@pytest.mark.asyncio
async def test_list_users(client: AsyncClient):
    # Create a user first
    await client.post(
        "/users",
        json={
            "username": "listuser",
            "email": "list@test.com",
            "password": "securepassword123",
            "role": "viewer",
        },
    )

    response = await client.get("/users")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_export_logs(client: AsyncClient, sample_audit_log: dict):
    response = await client.get("/logs/export")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    content = response.text
    assert "id" in content
    assert "timestamp" in content


@pytest.mark.asyncio
async def test_stats_timeline(client: AsyncClient, sample_audit_log: dict):
    response = await client.get("/stats/timeline")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 24


@pytest.mark.asyncio
async def test_stats_by_provider(client: AsyncClient, sample_audit_log: dict):
    response = await client.get("/stats/by-provider")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["provider"] == "openai"
