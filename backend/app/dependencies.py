"""
ClairEat Backend — FastAPI Dependency Injection
Provides reusable dependency functions for auth, DB, services.
"""

from typing import Annotated

from fastapi import Depends, Header
from supabase import AsyncClient

from app.config import Settings, get_settings
from app.core.exceptions import UnauthorizedError
from app.core.logging import get_logger
from app.core.supabase_client import get_supabase

logger = get_logger(__name__)


async def get_db(
    supabase: AsyncClient = Depends(get_supabase),
) -> AsyncClient:
    """Inject the Supabase async client."""
    return supabase


class CurrentUser:
    """Represents the authenticated caller extracted from the JWT."""

    def __init__(self, id: str, email: str) -> None:
        self.id = id
        self.email = email


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    db: AsyncClient = Depends(get_db),
) -> CurrentUser:
    """Validate the Authorization Bearer token against Supabase Auth.

    Extracts user identity from the JWT so that every downstream service
    can scope queries to the authenticated user without trusting request
    body data.

    Raises:
        UnauthorizedError: If the token is missing or invalid.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedError("Missing or malformed Authorization header.")

    token = authorization.split(" ", 1)[1]
    try:
        response = await db.auth.get_user(token)
        if response is None or response.user is None:
            raise UnauthorizedError("Token is invalid or expired.")
        user = response.user
        return CurrentUser(id=str(user.id), email=str(user.email))
    except UnauthorizedError:
        raise
    except Exception as exc:
        logger.error("Auth validation failed", error=str(exc))
        raise UnauthorizedError("Token validation failed.")


# ── Typed dependency aliases ───────────────────────────────────────────────────
DBDep = Annotated[AsyncClient, Depends(get_db)]
UserDep = Annotated[CurrentUser, Depends(get_current_user)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
