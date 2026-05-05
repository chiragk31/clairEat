"""
ClairEat Backend — Supabase Client Singleton
Provides a lazily initialised Supabase client using the Service Role key
for server-side operations (bypasses RLS where needed).
"""

from functools import lru_cache
from typing import Optional

from supabase import AsyncClient, acreate_client

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_supabase_client: Optional[AsyncClient] = None


async def get_supabase() -> AsyncClient:
    """Return the global Supabase async client, creating it if needed.

    Uses the Service Role key so that server-side writes (e.g. AI score
    updates, background jobs) are not blocked by RLS policies.
    Row-level data isolation is enforced separately in every query by
    filtering on ``user_id`` extracted from the validated JWT.
    """
    global _supabase_client
    if _supabase_client is None:
        settings = get_settings()
        logger.info("Initialising Supabase async client")
        _supabase_client = await acreate_client(
            settings.supabase_url,
            settings.supabase_service_role_key,
        )
    return _supabase_client


async def close_supabase() -> None:
    """Teardown — called during application shutdown lifespan."""
    global _supabase_client
    if _supabase_client is not None:
        logger.info("Closing Supabase client")
        # supabase-py AsyncClient doesn't expose explicit close; clear reference.
        _supabase_client = None
