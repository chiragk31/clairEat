"""Tests — Auth endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.dependencies import get_db


@pytest.fixture
async def unauthed_client():
    """Client with no auth override — for testing public auth endpoints."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


@pytest.mark.asyncio
async def test_register_success(unauthed_client):
    mock_db = MagicMock()
    mock_session = MagicMock(access_token="tok", refresh_token="ref", expires_in=3600)
    mock_user_obj = MagicMock(id="uuid-1")
    mock_resp = MagicMock(user=mock_user_obj, session=mock_session)
    mock_db.auth.sign_up = AsyncMock(return_value=mock_resp)

    app.dependency_overrides[get_db] = lambda: mock_db
    response = await unauthed_client.post("/v1/auth/register", json={
        "email": "new@test.com",
        "password": "Secure123!",
        "full_name": "Test User",
    })
    app.dependency_overrides.clear()

    assert response.status_code == 201
    data = response.json()
    assert data["access_token"] == "tok"
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_success(unauthed_client):
    mock_db = MagicMock()
    mock_session = MagicMock(access_token="access", refresh_token="refresh", expires_in=3600)
    mock_resp = MagicMock(user=MagicMock(id="uuid-1"), session=mock_session)
    mock_db.auth.sign_in_with_password = AsyncMock(return_value=mock_resp)

    app.dependency_overrides[get_db] = lambda: mock_db
    response = await unauthed_client.post("/v1/auth/login", json={
        "email": "user@test.com",
        "password": "password123",
    })
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["access_token"] == "access"


@pytest.mark.asyncio
async def test_login_invalid_credentials(unauthed_client):
    mock_db = MagicMock()
    mock_db.auth.sign_in_with_password = AsyncMock(side_effect=Exception("Invalid login credentials"))

    app.dependency_overrides[get_db] = lambda: mock_db
    response = await unauthed_client.post("/v1/auth/login", json={
        "email": "wrong@test.com",
        "password": "wrongpassword",
    })
    app.dependency_overrides.clear()

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_register_invalid_email(unauthed_client):
    response = await unauthed_client.post("/v1/auth/register", json={
        "email": "not-an-email",
        "password": "Secure123!",
    })
    assert response.status_code == 422  # Pydantic validation error
