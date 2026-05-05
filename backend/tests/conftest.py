"""
Tests — Shared Fixtures
Provides a reusable async test client and mock Supabase dependency override.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.dependencies import get_db, get_current_user, CurrentUser


# ── Mock user injected for protected route tests ───────────────────────────────

MOCK_USER_ID = "00000000-0000-0000-0000-000000000001"
MOCK_USER_EMAIL = "test@claireat.com"


def mock_user() -> CurrentUser:
    return CurrentUser(id=MOCK_USER_ID, email=MOCK_USER_EMAIL)


def build_mock_db() -> MagicMock:
    """Return a chainable MagicMock that simulates Supabase async responses."""
    db = MagicMock()
    # Default execute() returns empty data
    execute_mock = AsyncMock(return_value=MagicMock(data=[]))
    table_mock = MagicMock()
    table_mock.select.return_value = table_mock
    table_mock.insert.return_value = table_mock
    table_mock.update.return_value = table_mock
    table_mock.delete.return_value = table_mock
    table_mock.upsert.return_value = table_mock
    table_mock.eq.return_value = table_mock
    table_mock.gte.return_value = table_mock
    table_mock.lte.return_value = table_mock
    table_mock.order.return_value = table_mock
    table_mock.limit.return_value = table_mock
    table_mock.single.return_value = table_mock
    table_mock.is_.return_value = table_mock
    table_mock.ilike.return_value = table_mock
    table_mock.contains.return_value = table_mock
    table_mock.execute = execute_mock
    db.table.return_value = table_mock
    return db


@pytest.fixture
def mock_db():
    return build_mock_db()


@pytest.fixture
async def client(mock_db):
    """Async HTTP test client with auth and DB dependencies overridden."""
    app.dependency_overrides[get_current_user] = mock_user
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c
    app.dependency_overrides.clear()
