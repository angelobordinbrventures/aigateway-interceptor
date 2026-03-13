import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.database.connection import Base, get_db
from api.main import app

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session_factory = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with test_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_token(client: AsyncClient) -> str:
    """Create a seed admin user directly in DB and return a JWT token."""
    from api.database.models import User
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    async with test_session_factory() as session:
        user = User(
            username="seedadmin",
            email="seed@test.com",
            hashed_password=pwd_context.hash("securepassword123"),
            role="admin",
        )
        session.add(user)
        await session.commit()

    response = await client.post(
        "/auth/token",
        json={"username": "seedadmin", "password": "securepassword123"},
    )
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def auth_headers(auth_token: str) -> dict:
    return {"Authorization": f"Bearer {auth_token}"}


@pytest_asyncio.fixture
async def sample_policy(client: AsyncClient) -> dict:
    response = await client.post(
        "/policies",
        json={
            "name": "Block PII to OpenAI",
            "description": "Blocks requests containing PII to OpenAI",
            "ai_targets": ["openai"],
            "finding_categories": ["pii", "ssn"],
            "action": "block",
            "priority": 10,
            "enabled": True,
        },
    )
    return response.json()


@pytest_asyncio.fixture
async def sample_audit_log(client: AsyncClient) -> dict:
    response = await client.post(
        "/logs",
        json={
            "user_identifier": "testuser",
            "source_ip": "192.168.1.1",
            "ai_provider": "openai",
            "action_taken": "blocked",
            "findings": {"categories": ["ssn"], "count": 1},
            "request_hash": "abc123",
            "response_code": 200,
            "processing_time_ms": 12.5,
        },
    )
    return response.json()
