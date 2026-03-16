"""
Pytest fixtures for ByggSjekk API tests.

Uses SQLite in-memory for speed (unit tests) and can be configured to use
PostgreSQL for integration tests via TEST_DATABASE_URL env var.
"""
from __future__ import annotations
import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Use SQLite for tests unless TEST_DATABASE_URL is set
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create async engine with SQLite in-memory for tests."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )
    # Create all tables
    from app.db.base import Base
    import app.models  # noqa: F401 – registers all models
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db(test_engine):
    """Provide a test database session with rollback after each test."""
    async_session = async_sessionmaker(test_engine, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db):
    """Provide an async test client with DB override."""
    from main import create_app
    from app.core.deps import get_db

    app = create_app()

    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def registered_user(client):
    """Register and return a test user."""
    response = await client.post("/api/v1/auth/register", json={
        "email": "testarkitekt@byggsjekk.no",
        "password": "TestPassord123!",
        "full_name": "Test Arkitekt",
    })
    assert response.status_code == 201, response.text
    return response.json()


@pytest_asyncio.fixture
async def auth_headers(client, registered_user):
    """Return auth headers for the test user."""
    response = await client.post("/api/v1/auth/login", data={
        "username": "testarkitekt@byggsjekk.no",
        "password": "TestPassord123!",
    })
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def sample_property(db):
    """Create and return a sample Property row directly in the DB."""
    import uuid
    from app.models.property_case import Property

    prop = Property(
        id=uuid.uuid4(),
        street_address="Storgata 1",
        postal_code="0155",
        municipality="Oslo",
        gnr=207,
        bnr=123,
    )
    db.add(prop)
    await db.flush()
    await db.refresh(prop)
    return prop


@pytest_asyncio.fixture
async def sample_case(client, auth_headers, sample_property):
    """Create and return a sample property case."""
    response = await client.post("/api/v1/cases", json={
        "title": "Testinnbygging – Storgata 1",
        "customer_type": "PRIVATE",
        "intake_source": "web",
        "property_id": str(sample_property.id),
    }, headers=auth_headers)
    assert response.status_code == 201, response.text
    return response.json()
