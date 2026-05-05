"""
ClairEat — Open Food Facts API Client
Primary source for packaged food data and barcode lookups.
"""

from typing import Any, Dict, List, Optional

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import get_settings
from app.core.exceptions import ExternalAPIError
from app.core.logging import get_logger

logger = get_logger(__name__)


def _normalize_off_product(product: Dict[str, Any]) -> Dict[str, Any]:
    """Normalise an Open Food Facts product dict to our internal schema."""
    nutriments = product.get("nutriments", {})
    return {
        "external_id": product.get("code") or product.get("_id"),
        "source": "open_food_facts",
        "name": (
            product.get("product_name")
            or product.get("product_name_en")
            or "Unknown"
        ).strip(),
        "brand": product.get("brands", "").split(",")[0].strip() or None,
        "barcode": product.get("code") or None,
        "serving_size_g": _safe_float(product.get("serving_quantity")),
        "serving_unit": product.get("serving_size"),
        "calories_per_100g": _safe_float(nutriments.get("energy-kcal_100g")),
        "protein_per_100g": _safe_float(nutriments.get("proteins_100g")),
        "carbs_per_100g": _safe_float(nutriments.get("carbohydrates_100g")),
        "fat_per_100g": _safe_float(nutriments.get("fat_100g")),
        "fiber_per_100g": _safe_float(nutriments.get("fiber_100g")),
        "sugar_per_100g": _safe_float(nutriments.get("sugars_100g")),
        "sodium_per_100g": _safe_float(nutriments.get("sodium_100g")),
        "nutriscore": product.get("nutriscore_grade", "").upper() or None,
        "nova_group": _safe_int(product.get("nova_group")),
        "allergens": [
            a.strip()
            for a in product.get("allergens_tags", [])
            if a.strip()
        ],
        "image_url": product.get("image_front_url") or product.get("image_url"),
        "vitamins": {},
        "minerals": {},
    }


def _safe_float(value: Any) -> Optional[float]:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _safe_int(value: Any) -> Optional[int]:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


class OpenFoodFactsClient:
    """Async client for the Open Food Facts public API."""

    def __init__(self) -> None:
        settings = get_settings()
        self._base = settings.open_food_facts_base
        self._headers = {
            "User-Agent": "ClairEat/1.0 (https://claireat.com; contact@claireat.com)"
        }

    @retry(
        retry=retry_if_exception_type(httpx.TransportError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, max=4),
    )
    async def search(
        self, query: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Full-text food search via Open Food Facts.

        Args:
            query: Search term (food name, brand, etc.)
            limit: Maximum number of results to return.

        Returns:
            List of normalised food item dicts.
        """
        url = f"{self._base}/cgi/search.pl"
        params = {
            "search_terms": query,
            "search_simple": 1,
            "action": "process",
            "json": 1,
            "page_size": limit,
            "fields": (
                "code,product_name,product_name_en,brands,nutriments,"
                "nutriscore_grade,nova_group,allergens_tags,serving_quantity,"
                "serving_size,image_front_url,energy-kcal_100g"
            ),
        }
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url, params=params, headers=self._headers)
                resp.raise_for_status()
                data = resp.json()
                products = data.get("products", [])
                return [_normalize_off_product(p) for p in products if p.get("product_name")]
        except httpx.HTTPStatusError as exc:
            raise ExternalAPIError(
                f"HTTP {exc.response.status_code}", "Open Food Facts"
            ) from exc
        except Exception as exc:
            logger.warning("Open Food Facts search failed", query=query, error=str(exc))
            return []

    @retry(
        retry=retry_if_exception_type(httpx.TransportError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, max=4),
    )
    async def lookup_barcode(self, barcode: str) -> Optional[Dict[str, Any]]:
        """Look up a product by EAN/UPC barcode.

        Returns:
            Normalised food dict or None if not found.
        """
        url = f"{self._base}/api/v2/product/{barcode}"
        params = {"fields": "product_name,brands,nutriments,nutriscore_grade,nova_group,allergens_tags,serving_quantity,image_front_url,code"}
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url, params=params, headers=self._headers)
                if resp.status_code == 404:
                    return None
                resp.raise_for_status()
                data = resp.json()
                if data.get("status") != 1:
                    return None
                product = data.get("product", {})
                product["code"] = barcode
                return _normalize_off_product(product)
        except httpx.HTTPStatusError:
            return None
        except Exception as exc:
            logger.warning("Barcode lookup failed", barcode=barcode, error=str(exc))
            return None
