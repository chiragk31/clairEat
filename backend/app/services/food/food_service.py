"""
ClairEat — Unified Food Search Service
Cascade: Supabase cache → Open Food Facts + USDA (parallel) → Nutritionix
Deduplication, ranking, and persistent caching.
"""

import asyncio
import hashlib
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from supabase import AsyncClient

from app.core.cache import cache_manager
from app.core.logging import get_logger
from app.services.food.nutritionix import NutritionixClient
from app.services.food.open_food_facts import OpenFoodFactsClient
from app.services.food.usda_service import USDAService

logger = get_logger(__name__)

_off_client = OpenFoodFactsClient()
_usda_client = USDAService()
_nlp_client = NutritionixClient()


def _cache_key(query: str) -> str:
    return "food:" + hashlib.md5(query.lower().strip().encode()).hexdigest()


def _deduplicate(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate food items by name similarity (case-insensitive)."""
    seen: set[str] = set()
    unique = []
    for item in results:
        key = item["name"].lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def _rank(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Rank results: prefer items with complete nutrition data."""
    def score(item: Dict[str, Any]) -> int:
        s = 0
        if item.get("calories_per_100g") is not None:
            s += 3
        if item.get("protein_per_100g") is not None:
            s += 2
        if item.get("carbs_per_100g") is not None:
            s += 1
        if item.get("nutriscore"):
            s += 1
        return s
    return sorted(results, key=score, reverse=True)


class FoodSearchService:
    """Multi-source food search with cascade, deduplication, and caching.

    Search order:
    1. L1 in-memory TTLCache
    2. L2 Supabase food_items table (persistent)
    3. Fan-out to Open Food Facts + USDA in parallel
    4. Nutritionix (if still under limit after above)
    """

    def __init__(self, db: AsyncClient) -> None:
        self._db = db

    async def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Unified food search across all sources."""
        cache_key = _cache_key(query)

        # L1 Cache
        cached = await cache_manager.get_food(cache_key)
        if cached is not None:
            logger.debug("L1 cache hit", query=query)
            return cached[:limit]

        # L2 Supabase full-text search
        db_results = await self._search_db(query, limit)
        if len(db_results) >= limit:
            await cache_manager.set_food(cache_key, db_results)
            return db_results[:limit]

        # Fan-out to external APIs concurrently
        ext_results_raw = await asyncio.gather(
            _off_client.search(query, limit),
            _usda_client.search(query, limit),
            return_exceptions=True,
        )
        merged: List[Dict[str, Any]] = list(db_results)
        for res in ext_results_raw:
            if isinstance(res, list):
                merged.extend(res)

        # Deduplicate, rank
        merged = _rank(_deduplicate(merged))

        # Persist new items to Supabase (background, non-blocking)
        asyncio.create_task(self._cache_to_db(merged))

        # Set L1 cache
        await cache_manager.set_food(cache_key, merged)
        return merged[:limit]

    async def lookup_barcode(self, barcode: str) -> Optional[Dict[str, Any]]:
        """Barcode lookup — Supabase then Open Food Facts."""
        # Check DB first
        try:
            resp = await self._db.table("food_items").select("*").eq("barcode", barcode).limit(1).execute()
            if resp.data:
                return resp.data[0]
        except Exception:
            pass

        # Fetch from Open Food Facts
        item = await _off_client.lookup_barcode(barcode)
        if item:
            asyncio.create_task(self._cache_to_db([item]))
        return item

    async def natural_language_parse(self, text: str) -> List[Dict[str, Any]]:
        """Parse natural language food descriptions via Nutritionix."""
        return await _nlp_client.natural_language_parse(text)

    async def get_by_id(self, food_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a food item by its Supabase UUID."""
        try:
            resp = await self._db.table("food_items").select("*").eq("id", food_id).single().execute()
            return resp.data
        except Exception:
            return None

    async def save_custom_food(self, user_id: str, food_data: Dict[str, Any]) -> Dict[str, Any]:
        """Persist a user-defined custom food item."""
        food_data["source"] = "user"
        food_data["is_verified"] = False
        food_data["created_at"] = datetime.utcnow().isoformat()
        resp = await self._db.table("food_items").insert(food_data).execute()
        return resp.data[0]

    async def get_user_favorites(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Return user's favourite / most-logged foods."""
        resp = (
            await self._db.table("user_foods")
            .select("*, food_items(*)")
            .eq("user_id", user_id)
            .order("times_logged", desc=True)
            .limit(limit)
            .execute()
        )
        return [r["food_items"] for r in (resp.data or []) if r.get("food_items")]

    async def get_user_food_history(self, user_id: str, limit: int = 30) -> List[Dict[str, Any]]:
        """Return recently logged distinct foods for the user."""
        resp = (
            await self._db.table("meal_log_items")
            .select("food_item_id, food_items(name, calories_per_100g, protein_per_100g)")
            .eq("meal_logs.user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        seen: set = set()
        result = []
        for r in resp.data or []:
            fi = r.get("food_items")
            if fi and r.get("food_item_id") not in seen:
                seen.add(r["food_item_id"])
                result.append(fi)
        return result

    # ── Private Helpers ───────────────────────────────────────────────────

    async def _search_db(self, query: str, limit: int) -> List[Dict[str, Any]]:
        try:
            resp = (
                await self._db.table("food_items")
                .select("*")
                .ilike("name", f"%{query}%")
                .limit(limit)
                .execute()
            )
            return resp.data or []
        except Exception as exc:
            logger.warning("DB food search failed", error=str(exc))
            return []

    async def _cache_to_db(self, items: List[Dict[str, Any]]) -> None:
        """Insert new food items into the Supabase L2 cache (upsert by name+source)."""
        for item in items:
            if not item.get("name"):
                continue
            try:
                await self._db.table("food_items").upsert(
                    {**item, "created_at": datetime.utcnow().isoformat()},
                    on_conflict="external_id,source",
                    ignore_duplicates=True,
                ).execute()
            except Exception:
                pass  # Non-critical background operation
