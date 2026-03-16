"""Tests for review and report endpoints."""
from __future__ import annotations

import pytest
import pytest_asyncio


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _make_architect(db):
    """Return an architect user for tests requiring architect privileges."""
    from app.models.user import User
    from app.core.security import get_password_hash
    import uuid

    architect = User(
        id=uuid.uuid4(),
        email=f"arkitekt_{uuid.uuid4().hex[:6]}@byggsjekk.no",
        hashed_password=get_password_hash("ArkitektPassord123!"),
        full_name="Test Arkitekt",
        is_architect=True,
    )
    db.add(architect)
    await db.flush()
    return architect


async def _get_architect_headers(client, architect):
    """Log in as the architect and return auth headers."""
    response = await client.post("/api/v1/auth/login", data={
        "username": architect.email,
        "password": "ArkitektPassord123!",
    })
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Review tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_review_not_found(client, auth_headers, sample_case):
    """Getting a review when none exists returns 404."""
    case_id = sample_case["id"]
    response = await client.get(
        f"/api/v1/cases/{case_id}/review",
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_review_requires_architect(client, auth_headers, sample_case):
    """Non-architect users cannot create reviews (403)."""
    case_id = sample_case["id"]
    response = await client.post(
        f"/api/v1/cases/{case_id}/review",
        json={"comments": "Test kommentar"},
        headers=auth_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_review_as_architect(client, sample_case, db):
    """Architects can create a review for a case."""
    architect = await _make_architect(db)
    headers = await _get_architect_headers(client, architect)

    case_id = sample_case["id"]
    response = await client.post(
        f"/api/v1/cases/{case_id}/review",
        json={"comments": "Ser bra ut, men avvik bør sjekkes."},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert "id" in data
    assert data["case_id"] == case_id
    assert data["comments"] == "Ser bra ut, men avvik bør sjekkes."
    assert data["status"] == "PENDING"


@pytest.mark.asyncio
async def test_get_review_after_creation(client, sample_case, db):
    """After creating a review, GET returns it."""
    architect = await _make_architect(db)
    headers = await _get_architect_headers(client, architect)
    case_id = sample_case["id"]

    # Create review
    await client.post(
        f"/api/v1/cases/{case_id}/review",
        json={"comments": "Initial review"},
        headers=headers,
    )

    # Fetch it
    response = await client.get(
        f"/api/v1/cases/{case_id}/review",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == case_id


@pytest.mark.asyncio
async def test_update_review_as_architect(client, sample_case, db):
    """Architects can update a review."""
    architect = await _make_architect(db)
    headers = await _get_architect_headers(client, architect)
    case_id = sample_case["id"]

    # Create review first
    await client.post(
        f"/api/v1/cases/{case_id}/review",
        json={},
        headers=headers,
    )

    # Update it
    response = await client.patch(
        f"/api/v1/cases/{case_id}/review",
        json={"comments": "Oppdatert kommentar", "status": "IN_PROGRESS"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["comments"] == "Oppdatert kommentar"


# ---------------------------------------------------------------------------
# Report tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_report_not_found(client, auth_headers, sample_case):
    """Getting a report when none exists returns 404."""
    case_id = sample_case["id"]
    response = await client.get(
        f"/api/v1/cases/{case_id}/report",
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_report_requires_architect(client, auth_headers, sample_case):
    """Non-architect users cannot create reports (403)."""
    case_id = sample_case["id"]
    response = await client.post(
        f"/api/v1/cases/{case_id}/report",
        json={"report_type": "INTERNAL", "content": {}},
        headers=auth_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_report_as_architect(client, sample_case, db):
    """Architects can create a report for a case."""
    architect = await _make_architect(db)
    headers = await _get_architect_headers(client, architect)
    case_id = sample_case["id"]

    response = await client.post(
        f"/api/v1/cases/{case_id}/report",
        json={
            "report_type": "INTERNAL",
            "content": {"tittel": "Test rapport", "avvik": []},
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["case_id"] == case_id
    assert data["report_type"] == "INTERNAL"
    assert data["version"] == 1


@pytest.mark.asyncio
async def test_generate_report_as_architect(client, sample_case, db):
    """POST /report/generate creates a new AI-generated report."""
    architect = await _make_architect(db)
    headers = await _get_architect_headers(client, architect)
    case_id = sample_case["id"]

    response = await client.post(
        f"/api/v1/cases/{case_id}/report/generate",
        headers=headers,
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["case_id"] == case_id
    assert "content" in data
    assert "tittel" in data["content"]
    assert "fraskrivelse" in data["content"]


@pytest.mark.asyncio
async def test_report_versioning(client, sample_case, db):
    """Creating multiple reports increments the version number."""
    architect = await _make_architect(db)
    headers = await _get_architect_headers(client, architect)
    case_id = sample_case["id"]

    resp1 = await client.post(
        f"/api/v1/cases/{case_id}/report",
        json={"report_type": "INTERNAL", "content": {}},
        headers=headers,
    )
    resp2 = await client.post(
        f"/api/v1/cases/{case_id}/report",
        json={"report_type": "CUSTOMER", "content": {}},
        headers=headers,
    )
    assert resp1.status_code == 201
    assert resp2.status_code == 201
    assert resp1.json()["version"] == 1
    assert resp2.json()["version"] == 2


@pytest.mark.asyncio
async def test_approve_report(client, sample_case, db):
    """Architects can approve an existing report."""
    architect = await _make_architect(db)
    headers = await _get_architect_headers(client, architect)
    case_id = sample_case["id"]

    # Create report first
    await client.post(
        f"/api/v1/cases/{case_id}/report",
        json={"report_type": "INTERNAL", "content": {}},
        headers=headers,
    )

    # Approve it
    response = await client.post(
        f"/api/v1/cases/{case_id}/report/approve",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["approved_at"] is not None
    assert data["approved_by_id"] == str(architect.id)


@pytest.mark.asyncio
async def test_approve_already_approved_report_returns_409(client, sample_case, db):
    """Approving an already-approved report returns 409 Conflict."""
    architect = await _make_architect(db)
    headers = await _get_architect_headers(client, architect)
    case_id = sample_case["id"]

    # Create and approve
    await client.post(
        f"/api/v1/cases/{case_id}/report",
        json={"report_type": "INTERNAL", "content": {}},
        headers=headers,
    )
    await client.post(f"/api/v1/cases/{case_id}/report/approve", headers=headers)

    # Try to approve again
    response = await client.post(
        f"/api/v1/cases/{case_id}/report/approve",
        headers=headers,
    )
    assert response.status_code == 409
