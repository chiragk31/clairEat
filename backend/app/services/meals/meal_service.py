"""
ClairEat — Meal Service
CRUD for meal logs, macro aggregation, daily summary, and photo uploads.
"""

import asyncio
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from supabase import AsyncClient

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.schemas.meal import LogMealRequest
from app.utils.nutrition_utils import calculate_meal_item_nutrition, sum_macros, pct_of_target, water_target_ml

logger = get_logger(__name__)


class MealService:
    """Handles all meal logging business logic."""

    def __init__(self, db: AsyncClient) -> None:
        self._db = db

    async def log_meal(
        self, user_id: str, request: LogMealRequest
    ) -> Dict[str, Any]:
        """Log a complete meal with all food items.

        1. Resolve nutrition for each item from food_items table or custom values.
        2. Compute meal-level macro totals.
        3. Insert meal_log + meal_log_items atomically.
        4. Update global logging streak.

        Returns the created meal log with computed totals.
        """
        items_with_nutrition = await self._resolve_items(request.items)
        totals = sum_macros(items_with_nutrition)

        # Insert meal log row
        meal_row = {
            "user_id": user_id,
            "meal_date": str(request.meal_date),
            "meal_type": request.meal_type,
            "mood_before": request.mood_before,
            "mood_after": request.mood_after,
            "hunger_level_before": request.hunger_level_before,
            "fullness_level_after": request.fullness_level_after,
            "location": request.location,
            "notes": request.notes,
            "total_calories": totals["calories"],
            "total_protein_g": totals["protein_g"],
            "total_carbs_g": totals["carbs_g"],
            "total_fat_g": totals["fat_g"],
            "total_fiber_g": totals["fiber_g"],
            "logged_at": datetime.utcnow().isoformat(),
        }
        resp = await self._db.table("meal_logs").insert(meal_row).execute()
        meal_log = resp.data[0]
        meal_log_id = meal_log["id"]

        # Insert food items
        item_rows = [
            {
                "meal_log_id": meal_log_id,
                "food_item_id": item.get("food_item_id"),
                "custom_food_name": item.get("custom_food_name"),
                "quantity_g": item["quantity_g"],
                "calories": item["calories"],
                "protein_g": item["protein_g"],
                "carbs_g": item["carbs_g"],
                "fat_g": item["fat_g"],
                "fiber_g": item["fiber_g"],
            }
            for item in items_with_nutrition
        ]
        await self._db.table("meal_log_items").insert(item_rows).execute()

        # Update global logging streak asynchronously
        asyncio.create_task(self._update_logging_streak(user_id, request.meal_date))

        return {
            "meal_log_id": meal_log_id,
            "total_calories": totals["calories"],
            "total_protein_g": totals["protein_g"],
            "total_carbs_g": totals["carbs_g"],
            "total_fat_g": totals["fat_g"],
        }

    async def get_today_meals(self, user_id: str) -> Dict[str, Any]:
        """Fetch all meal logs for today."""
        today = str(date.today())
        return await self.get_meals_for_date(user_id, today)

    async def get_meals_for_date(self, user_id: str, meal_date: str) -> Dict[str, Any]:
        """Fetch all meal logs for a specific date, including items."""
        resp = (
            await self._db.table("meal_logs")
            .select("*, meal_log_items(*)")
            .eq("user_id", user_id)
            .eq("meal_date", meal_date)
            .order("logged_at")
            .execute()
        )
        return {"date": meal_date, "meals": resp.data or []}

    async def get_meal_by_id(self, user_id: str, meal_id: str) -> Dict[str, Any]:
        """Fetch a single meal log with its items."""
        resp = (
            await self._db.table("meal_logs")
            .select("*, meal_log_items(*)")
            .eq("id", meal_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        if not resp.data:
            raise NotFoundError(f"Meal log {meal_id} not found.")
        return resp.data

    async def delete_meal(self, user_id: str, meal_id: str) -> None:
        """Delete a meal log (cascade deletes items via FK)."""
        resp = (
            await self._db.table("meal_logs")
            .delete()
            .eq("id", meal_id)
            .eq("user_id", user_id)
            .execute()
        )
        if not resp.data:
            raise NotFoundError(f"Meal log {meal_id} not found.")

    async def get_daily_summary(self, user_id: str) -> Dict[str, Any]:
        """Aggregated macro totals vs user targets for today."""
        today = str(date.today())
        resp = (
            await self._db.table("meal_logs")
            .select("total_calories, total_protein_g, total_carbs_g, total_fat_g, total_fiber_g")
            .eq("user_id", user_id)
            .eq("meal_date", today)
            .execute()
        )
        meals = resp.data or []
        totals = sum_macros([
            {
                "calories": m["total_calories"],
                "protein_g": m["total_protein_g"],
                "carbs_g": m["total_carbs_g"],
                "fat_g": m["total_fat_g"],
                "fiber_g": m["total_fiber_g"],
            }
            for m in meals
        ])

        # Fetch profile targets
        profile = await self._get_profile(user_id)
        cal_target = float(profile.get("daily_calorie_target") or 2000)
        pro_target = float(profile.get("daily_protein_target_g") or 100)
        carb_target = float(profile.get("daily_carb_target_g") or 250)
        fat_target = float(profile.get("daily_fat_target_g") or 65)

        # Water total for today
        water_resp = (
            await self._db.table("water_logs")
            .select("amount_ml")
            .eq("user_id", user_id)
            .eq("log_date", today)
            .execute()
        )
        water_ml = sum(w["amount_ml"] for w in (water_resp.data or []))
        w_kg = float(profile.get("weight_kg") or 70)
        water_target = water_target_ml(w_kg)

        return {
            "date": today,
            "totals": {
                "calories": totals["calories"],
                "protein_g": totals["protein_g"],
                "carbs_g": totals["carbs_g"],
                "fat_g": totals["fat_g"],
            },
            "targets": {
                "calories": cal_target,
                "protein_g": pro_target,
                "carbs_g": carb_target,
                "fat_g": fat_target,
            },
            "pct_complete": {
                "calories": pct_of_target(totals["calories"], cal_target),
                "protein": pct_of_target(totals["protein_g"], pro_target),
                "carbs": pct_of_target(totals["carbs_g"], carb_target),
                "fat": pct_of_target(totals["fat_g"], fat_target),
            },
            "water_ml": water_ml,
            "water_target_ml": water_target,
        }

    async def get_meal_history(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """Return macro totals grouped by date for the past N days."""
        from datetime import timedelta
        start_date = str(date.today() - timedelta(days=days - 1))
        resp = (
            await self._db.table("meal_logs")
            .select("meal_date, total_calories, total_protein_g, total_carbs_g, total_fat_g")
            .eq("user_id", user_id)
            .gte("meal_date", start_date)
            .order("meal_date", desc=True)
            .execute()
        )
        # Group by date
        by_date: Dict[str, Dict] = {}
        for row in resp.data or []:
            d = row["meal_date"]
            if d not in by_date:
                by_date[d] = {"date": d, "calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0}
            by_date[d]["calories"] += row["total_calories"] or 0
            by_date[d]["protein_g"] += row["total_protein_g"] or 0
            by_date[d]["carbs_g"] += row["total_carbs_g"] or 0
            by_date[d]["fat_g"] += row["total_fat_g"] or 0

        day_list = sorted(by_date.values(), key=lambda x: x["date"], reverse=True)
        return {"days": day_list, "total_days": len(day_list)}

    async def update_ai_score(
        self, meal_log_id: str, score: float, feedback: str
    ) -> None:
        """Update a meal log with AI scoring results (called asynchronously)."""
        await self._db.table("meal_logs").update(
            {"ai_meal_score": score, "ai_feedback": feedback}
        ).eq("id", meal_log_id).execute()

    # ── Private Helpers ───────────────────────────────────────────────────

    async def _resolve_items(self, items: list) -> List[Dict[str, Any]]:
        """Compute nutrition for each meal item."""
        resolved = []
        for item in items:
            if item.food_item_id:
                resp = (
                    await self._db.table("food_items")
                    .select("calories_per_100g, protein_per_100g, carbs_per_100g, fat_per_100g, fiber_per_100g")
                    .eq("id", item.food_item_id)
                    .single()
                    .execute()
                )
                food = resp.data or {}
                nutrition = calculate_meal_item_nutrition(food, item.quantity_g)
            else:
                # Custom food — trust submitted values, scale to 100g base
                nutrition = {
                    "calories": float(item.calories or 0),
                    "protein_g": float(item.protein_g or 0),
                    "carbs_g": float(item.carbs_g or 0),
                    "fat_g": float(item.fat_g or 0),
                    "fiber_g": float(item.fiber_g or 0),
                }
            resolved.append({
                "food_item_id": item.food_item_id,
                "custom_food_name": item.custom_food_name,
                "quantity_g": item.quantity_g,
                **nutrition,
            })
        return resolved

    async def _get_profile(self, user_id: str) -> Dict[str, Any]:
        try:
            resp = await self._db.table("profiles").select("*").eq("id", user_id).single().execute()
            return resp.data or {}
        except Exception:
            return {}

    async def _update_logging_streak(self, user_id: str, log_date: date) -> None:
        """Update or create the global meal-logging streak for the user."""
        try:
            resp = (
                await self._db.table("streaks")
                .select("*")
                .eq("user_id", user_id)
                .eq("streak_type", "logging")
                .is_("habit_id", "null")
                .limit(1)
                .execute()
            )
            streaks = resp.data or []
            from datetime import timedelta
            yesterday = date.today() - timedelta(days=1)
            today = date.today()

            if streaks:
                streak = streaks[0]
                last = streak.get("last_activity_date")
                last_date = date.fromisoformat(last) if last else None
                if last_date == today:
                    return  # Already updated today
                if last_date == yesterday:
                    new_streak = streak["current_streak"] + 1
                else:
                    new_streak = 1
                longest = max(new_streak, streak.get("longest_streak", 0))
                await self._db.table("streaks").update({
                    "current_streak": new_streak,
                    "longest_streak": longest,
                    "last_activity_date": str(today),
                    "updated_at": datetime.utcnow().isoformat(),
                }).eq("id", streak["id"]).execute()
            else:
                await self._db.table("streaks").insert({
                    "user_id": user_id,
                    "streak_type": "logging",
                    "current_streak": 1,
                    "longest_streak": 1,
                    "last_activity_date": str(today),
                    "updated_at": datetime.utcnow().isoformat(),
                }).execute()
        except Exception as exc:
            logger.warning("Failed to update logging streak", error=str(exc))
