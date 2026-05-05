"""
ClairEat — USDA FoodData Central API Client
Best source for whole foods and accurate nutritional data.
"""

from typing import Any, Dict, List, Optional

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.core.exceptions import ExternalAPIError
from app.core.logging import get_logger

logger = get_logger(__name__)

USDA_BASE = "https://api.nal.usda.gov/fdc/v1"


def _extract_nutrient(food_nutrients: List[Dict], nutrient_id: int) -> Optional[float]:
    """Extract a specific nutrient value by its FDC nutrient ID."""
    for n in food_nutrients:
        nid = (n.get("nutrient") or {}).get("id") or n.get("nutrientId")
        if nid == nutrient_id:
            return n.get("value") or n.get("amount")
    return None


# USDA FDC nutrient IDs
_NUT = {
    "calories_per_100g": 1008,    # Energy (kcal)
    "protein_per_100g": 1003,     # Protein
    "carbs_per_100g": 1005,       # Carbohydrate, by difference
    "fat_per_100g": 1004,         # Total lipid (fat)
    "fiber_per_100g": 1079,       # Fiber, total dietary
    "sugar_per_100g": 2000,       # Sugars, total
    "sodium_per_100g": 1093,      # Sodium
    "vitamin_c": 1162,
    "vitamin_d": 1114,
    "calcium": 1087,
    "iron": 1089,
    "potassium": 1092,
}


def _normalize_usda_food(food: Dict[str, Any]) -> Dict[str, Any]:
    nutrients = food.get("foodNutrients", [])
    vitamins = {}
    minerals = {}
    for name, nid in _NUT.items():
        if name.startswith("vitamin"):
            v = _extract_nutrient(nutrients, nid)
            if v is not None:
                vitamins[name] = v
        elif name in ("calcium", "iron", "potassium"):
            v = _extract_nutrient(nutrients, nid)
            if v is not None:
                minerals[name] = v

    return {
        "external_id": str(food.get("fdcId", "")),
        "source": "usda",
        "name": (food.get("description") or "Unknown").strip().title(),
        "brand": food.get("brandOwner") or food.get("brandName") or None,
        "barcode": food.get("gtinUpc") or None,
        "serving_size_g": food.get("servingSize"),
        "serving_unit": food.get("servingSizeUnit"),
        "calories_per_100g": _extract_nutrient(nutrients, _NUT["calories_per_100g"]),
        "protein_per_100g": _extract_nutrient(nutrients, _NUT["protein_per_100g"]),
        "carbs_per_100g": _extract_nutrient(nutrients, _NUT["carbs_per_100g"]),
        "fat_per_100g": _extract_nutrient(nutrients, _NUT["fat_per_100g"]),
        "fiber_per_100g": _extract_nutrient(nutrients, _NUT["fiber_per_100g"]),
        "sugar_per_100g": _extract_nutrient(nutrients, _NUT["sugar_per_100g"]),
        "sodium_per_100g": _extract_nutrient(nutrients, _NUT["sodium_per_100g"]),
        "vitamins": vitamins,
        "minerals": minerals,
        "nutriscore": None,
        "nova_group": None,
        "allergens": [],
        "image_url": None,
    }


class USDAService:
    """Async client for USDA FoodData Central API."""

    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.usda_api_key
        if not self._api_key:
            logger.warning("USDA_API_KEY not set — USDA service disabled")
        self._enabled = bool(self._api_key)

    @retry(
        retry=retry_if_exception_type(httpx.TransportError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, max=4),
    )
    async def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search USDA FoodData Central by food name."""
        if not self._enabled:
            return []
        url = f"{USDA_BASE}/foods/search"
        params = {
            "query": query,
            "pageSize": limit,
            "api_key": self._api_key,
            "dataType": "Foundation,SR Legacy,Branded",
        }
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                foods = data.get("foods", [])
                return [_normalize_usda_food(f) for f in foods]
        except httpx.HTTPStatusError as exc:
            raise ExternalAPIError(f"HTTP {exc.response.status_code}", "USDA") from exc
        except Exception as exc:
            logger.warning("USDA search failed", query=query, error=str(exc))
            return []
