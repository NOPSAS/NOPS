"""Tests for deviation CRUD endpoints."""
from __future__ import annotations

import pytest
import pytest_asyncio


@pytest.mark.asyncio
async def test_list_deviations_empty(client, auth_headers, sample_case):
    """Listing deviations for a case with no deviations returns empty list."""
    case_id = sample_case["id"]
    response = await client.get(
        f"/api/v1/cases/{case_id}/deviations",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_deviations_require_auth(client, sample_case):
    """Deviation listing requires authentication."""
    case_id = sample_case["id"]
    response = await client.get(f"/api/v1/cases/{case_id}/deviations")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_deviations_case_not_found(client, auth_headers):
    """Listing deviations for a non-existent case returns 404."""
    response = await client.get(
        "/api/v1/cases/00000000-0000-0000-0000-000000000000/deviations",
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_deviation_not_found(client, auth_headers, sample_case):
    """Fetching a non-existent deviation returns 404."""
    case_id = sample_case["id"]
    response = await client.get(
        f"/api/v1/cases/{case_id}/deviations/00000000-0000-0000-0000-000000000000",
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_deviation_requires_architect(client, auth_headers, sample_case, db):
    """Non-architect users cannot update deviations (403)."""
    from app.models.property_case import Deviation, DeviationCategory, Severity, DeviationStatus

    case_id = sample_case["id"]

    # Create a deviation directly in the DB
    import uuid
    dev = Deviation(
        id=uuid.uuid4(),
        case_id=uuid.UUID(case_id),
        category=DeviationCategory.ROOM_DEFINITION_CHANGE,
        severity=Severity.MEDIUM,
        description="Test avvik",
        confidence=0.75,
    )
    db.add(dev)
    await db.flush()

    response = await client.patch(
        f"/api/v1/cases/{case_id}/deviations/{dev.id}",
        json={"status": "REVIEWED", "architect_note": "Bekreftet avvik"},
        headers=auth_headers,
    )
    # Non-architects get 403 Forbidden
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_deviations_with_status_filter(client, auth_headers, sample_case, db):
    """Filtering deviations by status returns only matching deviations."""
    from app.models.property_case import Deviation, DeviationCategory, Severity, DeviationStatus

    case_id = sample_case["id"]
    import uuid

    # Create two deviations with different statuses
    dev_open = Deviation(
        id=uuid.uuid4(),
        case_id=uuid.UUID(case_id),
        category=DeviationCategory.ADDITION_DETECTED,
        severity=Severity.HIGH,
        description="Tilbygg oppdaget",
        confidence=0.90,
        status=DeviationStatus.OPEN,
    )
    dev_dismissed = Deviation(
        id=uuid.uuid4(),
        case_id=uuid.UUID(case_id),
        category=DeviationCategory.UNDERBUILDING_DETECTED,
        severity=Severity.LOW,
        description="Avvist avvik",
        confidence=0.50,
        status=DeviationStatus.DISMISSED,
    )
    db.add(dev_open)
    db.add(dev_dismissed)
    await db.flush()

    # Filter by OPEN
    response = await client.get(
        f"/api/v1/cases/{case_id}/deviations?status=OPEN",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert all(d["status"] == "OPEN" for d in data)

    # Filter by DISMISSED
    response_dismissed = await client.get(
        f"/api/v1/cases/{case_id}/deviations?status=DISMISSED",
        headers=auth_headers,
    )
    assert response_dismissed.status_code == 200
    data_dismissed = response_dismissed.json()
    assert all(d["status"] == "DISMISSED" for d in data_dismissed)
