"""
ClairEat — Nutritionix API Client
Best for natural language food parsing and restaurant/brand food data.
"""

from typing import Any, Dict, List, Optional

import httpx

from app.config import get_settings
from app.core.exceptions import ExternalAPIError
from app.core.logging import get_logger

logger = get_logger(__name__)

NUTRITIONIX_BASE = "https://trackapi.nutritionix.com/v2"


def _normalize_nutritionix_food(food: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "external_id": food.get("nix_item_id") or food.get("food_name"),
        "source": "nutritionix",
        "name": (food.get("food_name") or "Unknown").strip().title(),
        "brand": food.get("brand_name") or None,
        "barcode": food.get("upc") or None,
        "serving_size_g": food.get("serving_weight_grams"),
        "serving_unit": food.get("serving_unit"),
        "calories_per_100g": _per_100g(food.get("nf_calories"), food.get("serving_weight_grams")),
        "protein_per_100g": _per_100g(food.get("nf_protein"), food.get("serving_weight_grams")),
        "carbs_per_100g": _per_100g(food.get("nf_total_carbohydrate"), food.get("serving_weight_grams")),
        "fat_per_100g": _per_100g(food.get("nf_total_fat"), food.get("serving_weight_grams")),
        "fiber_per_100g": _per_100g(food.get("nf_dietary_fiber"), food.get("serving_weight_grams")),
        "sugar_per_100g": _per_100g(food.get("nf_sugars"), food.get("serving_weight_grams")),
        "sodium_per_100g": _per_100g(food.get("nf_sodium"), food.get("serving_weight_grams")),
        "vitamins": {},
        "minerals": {},
        "nutriscore": None,
        "nova_group": None,
        "allergens": [],
        "image_url": (food.get("photo") or {}).get("thumb"),
    }


def _per_100g(value: Optional[float], serving_g: Optional[float]) -> Optional[float]:
    if value is None or not serving_g or serving_g <= 0:
        return None
    return round((value / serving_g) * 100, 2)


class NutritionixClient:
    """Async client for Nutritionix — NLP parsing and search."""

    def __init__(self) -> None:
        settings = get_settings()
        self._app_id = settings.nutritionix_app_id
        self._app_key = settings.nutritionix_app_key
        self._enabled = bool(self._app_id and self._app_key)
        if not self._enabled:
            logger.warning("Nutritionix credentials not set — service disabled")

    def _headers(self) -> Dict[str, str]:
        return {
            "x-app-id": self._app_id,
            "x-app-key": self._app_key,
            "Content-Type": "application/json",
        }

    async def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Instant search (branded + common foods)."""
        if not self._enabled:
            return []
        url = f"{NUTRITIONIX_BASE}/search/instant"
        params = {"query": query, "branded": True, "common": True, "detailed": True}
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url, params=params, headers=self._headers())
                resp.raise_for_status()
                data = resp.json()
                results = []
                for food in (data.get("branded") or [])[:limit]:
                    results.append(_normalize_nutritionix_food(food))
                for food in (data.get("common") or [])[:max(0, limit - len(results))]:
                    results.append(_normalize_nutritionix_food(food))
                return results
        except httpx.HTTPStatusError as exc:
            raise ExternalAPIError(f"HTTP {exc.response.status_code}", "Nutritionix") from exc
        except Exception as exc:
            logger.warning("Nutritionix search failed", error=str(exc))
            return []

    async def natural_language_parse(self, text: str) -> List[Dict[str, Any]]:
        """Parse natural language input like '2 boiled eggs and a banana'.

        Nutritionix NLP endpoint is the best-in-class for this use-case.

        Returns:
            List of food items with computed per-serving nutrients.
        """
        if not self._enabled:
            return []
        url = f"{NUTRITIONIX_BASE}/natural/nutrients"
        body = {"query": text, "timezone": "US/Eastern"}
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(url, json=body, headers=self._headers())
                resp.raise_for_status()
                data = resp.json()
                foods = data.get("foods", [])
                return [
                    {
                        "name": f.get("food_name", "").title(),
                        "quantity_g": f.get("serving_weight_grams", 100),
                        "calories": f.get("nf_calories", 0),
                        "protein_g": f.get("nf_protein"),
                        "carbs_g": f.get("nf_total_carbohydrate"),
                        "fat_g": f.get("nf_total_fat"),
                    }
                    for f in foods
                ]
        except httpx.HTTPStatusError as exc:
            # 404/422 means unrecognised food — not a server error
            if exc.response.status_code in (404, 422):
                return []
            raise ExternalAPIError(f"HTTP {exc.response.status_code}", "Nutritionix") from exc
        except Exception as exc:
            logger.warning("Nutritionix NLP parse failed", text=text, error=str(exc))
            return []
