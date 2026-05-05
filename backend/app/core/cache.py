"""
ClairEat Backend — Multi-Layer Cache Manager
Two-tier caching strategy:
  L1 — in-memory TTLCache (no external dependency, sub-millisecond reads)
  L2 — Supabase food_items table (persistent across restarts)

No Redis required for early-stage deployment.
"""

import asyncio
from typing import Any, Optional

from cachetools import TTLCache

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class CacheManager:
    """Thread-safe (cooperative multitasking) in-memory TTL cache manager.

    Provides separate cache namespaces for food data, AI responses, and
    external API results (weather, exercise), each with independent TTLs.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._lock = asyncio.Lock()

        # Food search results — 24h TTL, max 5 000 items
        self._food: TTLCache = TTLCache(
            maxsize=settings.food_cache_max_size,
            ttl=settings.food_cache_ttl,
        )
        # AI response cache — 1h TTL (identical prompts, e.g. daily tip)
        self._ai: TTLCache = TTLCache(
            maxsize=settings.ai_cache_max_size,
            ttl=settings.ai_cache_ttl,
        )
        # External data — 6h TTL (weather, exercise)
        self._external: TTLCache = TTLCache(
            maxsize=settings.external_cache_max_size,
            ttl=settings.external_cache_ttl,
        )

    # ── Food Cache ────────────────────────────────────────────────────────

    async def get_food(self, key: str) -> Optional[Any]:
        async with self._lock:
            value = self._food.get(key)
        if value is not None:
            logger.debug("Cache hit [food]", key=key)
        return value

    async def set_food(self, key: str, value: Any) -> None:
        async with self._lock:
            self._food[key] = value
        logger.debug("Cache set [food]", key=key)

    async def delete_food(self, key: str) -> None:
        async with self._lock:
            self._food.pop(key, None)

    # ── AI Cache ──────────────────────────────────────────────────────────

    async def get_ai(self, key: str) -> Optional[Any]:
        async with self._lock:
            return self._ai.get(key)

    async def set_ai(self, key: str, value: Any) -> None:
        async with self._lock:
            self._ai[key] = value

    # ── External Cache ────────────────────────────────────────────────────

    async def get_external(self, key: str) -> Optional[Any]:
        async with self._lock:
            return self._external.get(key)

    async def set_external(self, key: str, value: Any) -> None:
        async with self._lock:
            self._external[key] = value

    # ── Stats ─────────────────────────────────────────────────────────────

    def stats(self) -> dict:
        """Return cache size statistics for observability."""
        return {
            "food": {"size": len(self._food), "maxsize": self._food.maxsize},
            "ai": {"size": len(self._ai), "maxsize": self._ai.maxsize},
            "external": {"size": len(self._external), "maxsize": self._external.maxsize},
        }


# Application-scoped singleton
cache_manager = CacheManager()
