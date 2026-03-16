"""Tests for document upload and management endpoints."""
from __future__ import annotations

import io
import pytest
import pytest_asyncio


@pytest.mark.asyncio
async def test_list_documents_empty(client, auth_headers, sample_case):
    """Listing documents for a case with no documents returns empty list."""
    case_id = sample_case["id"]
    response = await client.get(
        f"/api/v1/cases/{case_id}/documents",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_documents_requires_auth(client, sample_case):
    """Document listing requires authentication."""
    case_id = sample_case["id"]
    response = await client.get(f"/api/v1/cases/{case_id}/documents")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_documents_case_not_found(client, auth_headers):
    """Listing documents for a non-existent case returns 404."""
    response = await client.get(
        "/api/v1/cases/00000000-0000-0000-0000-000000000000/documents",
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_document_not_found(client, auth_headers, sample_case):
    """Fetching a non-existent document returns 404."""
    case_id = sample_case["id"]
    response = await client.get(
        f"/api/v1/cases/{case_id}/documents/00000000-0000-0000-0000-000000000000",
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_document_not_found(client, auth_headers, sample_case):
    """Deleting a non-existent document returns 404."""
    case_id = sample_case["id"]
    response = await client.delete(
        f"/api/v1/cases/{case_id}/documents/00000000-0000-0000-0000-000000000000",
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_upload_document_to_nonexistent_case(client, auth_headers):
    """Uploading to a non-existent case returns 404."""
    file_content = b"%PDF-1.4 test content"
    response = await client.post(
        "/api/v1/cases/00000000-0000-0000-0000-000000000000/documents",
        files={"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")},
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_upload_document_requires_auth(client, sample_case):
    """Document upload requires authentication."""
    case_id = sample_case["id"]
    file_content = b"%PDF-1.4 test content"
    response = await client.post(
        f"/api/v1/cases/{case_id}/documents",
        files={"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")},
    )
    assert response.status_code == 401
