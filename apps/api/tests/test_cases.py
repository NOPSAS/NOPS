"""Tests for property case CRUD endpoints."""
import pytest
import pytest_asyncio


@pytest_asyncio.fixture
async def parkveien_property(db):
    """Create a test property for Parkveien 10."""
    import uuid
    from app.models.property_case import Property

    prop = Property(
        id=uuid.uuid4(),
        street_address="Parkveien 10",
        postal_code="0350",
        municipality="Oslo",
        gnr=210,
        bnr=45,
    )
    db.add(prop)
    await db.flush()
    await db.refresh(prop)
    return prop


@pytest.mark.asyncio
async def test_create_case(client, auth_headers, parkveien_property):
    response = await client.post("/api/v1/cases", json={
        "title": "Kontroll av Parkveien 10",
        "customer_type": "PRIVATE",
        "intake_source": "web",
        "property_id": str(parkveien_property.id),
    }, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Kontroll av Parkveien 10"
    assert data["status"] == "DRAFT"


@pytest.mark.asyncio
async def test_list_cases(client, auth_headers, sample_case):
    response = await client.get("/api/v1/cases", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, (list, dict))
    # Handle both paginated and list responses
    cases = data.get("items", data) if isinstance(data, dict) else data
    assert len(cases) >= 1


@pytest.mark.asyncio
async def test_get_case(client, auth_headers, sample_case):
    case_id = sample_case["id"]
    response = await client.get(f"/api/v1/cases/{case_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == case_id


@pytest.mark.asyncio
async def test_get_case_not_found(client, auth_headers):
    response = await client.get("/api/v1/cases/00000000-0000-0000-0000-000000000000", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_case(client, auth_headers, sample_case):
    case_id = sample_case["id"]
    response = await client.patch(f"/api/v1/cases/{case_id}", json={
        "status": "ACTIVE",
    }, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "ACTIVE"


@pytest.mark.asyncio
async def test_cases_require_auth(client):
    response = await client.get("/api/v1/cases")
    assert response.status_code == 401
