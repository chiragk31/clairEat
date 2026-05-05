"""
ClairEat — Nutrition Calculation Utilities
Helper functions for macro/micro arithmetic used across services.
"""

from typing import Any, Dict, List, Optional


def scale_nutrition(per_100g: Optional[float], quantity_g: float) -> float:
    """Scale a per-100g nutrient value to an actual quantity.

    Returns 0.0 if the per-100g value is None (unknown nutrient).
    """
    if per_100g is None:
        return 0.0
    return round((per_100g * quantity_g) / 100, 2)


def sum_macros(items: List[Dict[str, Any]]) -> Dict[str, float]:
    """Aggregate macro totals across a list of meal log items.

    Each item dict is expected to have:
        calories, protein_g, carbs_g, fat_g, fiber_g
    """
    totals: Dict[str, float] = {
        "calories": 0.0,
        "protein_g": 0.0,
        "carbs_g": 0.0,
        "fat_g": 0.0,
        "fiber_g": 0.0,
    }
    for item in items:
        for key in totals:
            totals[key] += float(item.get(key) or 0)
    return {k: round(v, 2) for k, v in totals.items()}


def calculate_meal_item_nutrition(
    food: Dict[str, Any],
    quantity_g: float,
) -> Dict[str, float]:
    """Compute the actual nutrient values for a given quantity of a food item."""
    return {
        "calories": scale_nutrition(food.get("calories_per_100g"), quantity_g),
        "protein_g": scale_nutrition(food.get("protein_per_100g"), quantity_g),
        "carbs_g": scale_nutrition(food.get("carbs_per_100g"), quantity_g),
        "fat_g": scale_nutrition(food.get("fat_per_100g"), quantity_g),
        "fiber_g": scale_nutrition(food.get("fiber_per_100g"), quantity_g),
    }


def pct_of_target(actual: float, target: float) -> int:
    """Return percentage of target achieved, capped at 999%."""
    if target <= 0:
        return 0
    return min(int((actual / target) * 100), 999)


def water_target_ml(weight_kg: float) -> float:
    """Estimate daily water target: ~35 ml per kg body weight."""
    return round(weight_kg * 35, 0)
