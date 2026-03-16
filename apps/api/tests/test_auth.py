"""Tests for authentication endpoints."""
import pytest
import pytest_asyncio


@pytest.mark.asyncio
async def test_register_new_user(client):
    response = await client.post("/api/v1/auth/register", json={
        "email": "ny@byggsjekk.no",
        "password": "Passord123!",
        "full_name": "Ny Bruker",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "ny@byggsjekk.no"
    assert "id" in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client, registered_user):
    response = await client.post("/api/v1/auth/register", json={
        "email": "testarkitekt@byggsjekk.no",
        "password": "AnnetPassord123!",
        "full_name": "Duplikat",
    })
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client, registered_user):
    response = await client.post("/api/v1/auth/login", data={
        "username": "testarkitekt@byggsjekk.no",
        "password": "TestPassord123!",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client, registered_user):
    response = await client.post("/api/v1/auth/login", data={
        "username": "testarkitekt@byggsjekk.no",
        "password": "FeilPassord!",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client, auth_headers, registered_user):
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "testarkitekt@byggsjekk.no"


@pytest.mark.asyncio
async def test_me_unauthorized(client):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
