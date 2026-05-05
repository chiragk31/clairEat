"""
ClairEat — AI Meal Plan Generator
Generates a 7-day personalised meal plan and persists it to Supabase.
"""

from datetime import date, timedelta
from typing import Any, Dict, List

from supabase import AsyncClient

from app.core.exceptions import AIServiceError
from app.core.logging import get_logger
from app.services.ai.orchestrator import get_ai_orchestrator
from app.services.ai.prompt_builder import PromptBuilder
from app.services.ai.response_parser import parse_meal_plan

logger = get_logger(__name__)

DAYS_MAP = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


class MealPlanner:
    """Generates and persists AI meal plans."""

    def __init__(self, db: AsyncClient) -> None:
        self._db = db

    async def generate(
        self,
        user_id: str,
        start_date: str,
        preferences: Dict[str, Any],
        profile: Dict[str, Any],
        today_summary: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate a 7-day meal plan and save to Supabase.

        Args:
            user_id:       Authenticated user's UUID.
            start_date:    ISO date string for first day of plan.
            preferences:   Cuisine, excluded ingredients, max prep time.
            profile:       User profile dict (goals, targets, restrictions).
            today_summary: Today's macro totals (used for context).

        Returns:
            The generated meal plan with all days and entries.
        """
        user_context = PromptBuilder.build_user_context(
            profile=profile,
            today_summary=today_summary,
            recent_meals=[],
        )
        prompt = PromptBuilder.meal_plan_prompt(user_context, preferences)
        orchestrator = get_ai_orchestrator()
        provider = orchestrator.current_provider()

        try:
            raw = await orchestrator.generate_json(prompt)
            plan_data = parse_meal_plan(raw)
        except AIServiceError as exc:
            raise exc

        # Compute date range
        start = date.fromisoformat(start_date)
        end = start + timedelta(days=6)

        # Deactivate previous active plan
        await self._db.table("meal_plans").update({"is_active": False}).eq(
            "user_id", user_id
        ).eq("is_active", True).execute()

        # Insert meal_plans row
        plan_row = {
            "user_id": user_id,
            "plan_name": f"Week of {start.strftime('%B %d')}",
            "start_date": str(start),
            "end_date": str(end),
            "is_active": True,
            "target_calories": profile.get("daily_calorie_target", 2000),
            "generated_by": provider,
            "generation_context": {
                "preferences": preferences,
                "health_goals": profile.get("health_goals", []),
                "dietary_restrictions": profile.get("dietary_restrictions", []),
            },
        }
        plan_resp = await self._db.table("meal_plans").insert(plan_row).execute()
        meal_plan_id = plan_resp.data[0]["id"]

        # Insert meal_plan_entries
        days_out = []
        for day_data in plan_data.get("days", []):
            dow = day_data.get("day_of_week", 1)
            day_date = start + timedelta(days=dow - 1)
            day_total_cal = 0
            day_meals = []

            for meal in day_data.get("meals", []):
                entry_row = {
                    "meal_plan_id": meal_plan_id,
                    "day_of_week": dow,
                    "meal_type": meal.get("meal_type", "snack"),
                    "recipe_name": meal.get("recipe_name", ""),
                    "recipe_description": meal.get("recipe_description"),
                    "estimated_calories": meal.get("estimated_calories", 0),
                    "estimated_protein_g": meal.get("estimated_protein_g", 0),
                    "estimated_carbs_g": meal.get("estimated_carbs_g", 0),
                    "estimated_fat_g": meal.get("estimated_fat_g", 0),
                    "ingredients": meal.get("ingredients", []),
                    "preparation_steps": meal.get("preparation_steps", []),
                    "prep_time_minutes": meal.get("prep_time_minutes"),
                }
                await self._db.table("meal_plan_entries").insert(entry_row).execute()
                day_total_cal += meal.get("estimated_calories", 0)
                day_meals.append(meal)

            days_out.append({
                "day": day_data.get("day", DAYS_MAP[dow - 1]),
                "day_of_week": dow,
                "date": str(day_date),
                "meals": day_meals,
                "total_calories": day_total_cal,
            })

        return {
            "meal_plan_id": meal_plan_id,
            "plan_name": plan_row["plan_name"],
            "start_date": str(start),
            "end_date": str(end),
            "target_calories": plan_row["target_calories"],
            "generated_by": provider,
            "days": days_out,
        }

    async def get_shopping_list(self, meal_plan_id: str, user_id: str) -> Dict[str, Any]:
        """Aggregate ingredients across the plan into a categorised shopping list."""
        resp = (
            await self._db.table("meal_plan_entries")
            .select("ingredients")
            .eq("meal_plan_id", meal_plan_id)
            .execute()
        )
        # Aggregate by ingredient name
        agg: Dict[str, Dict[str, str]] = {}
        for entry in resp.data or []:
            for ing in (entry.get("ingredients") or []):
                name = ing.get("name", "").strip().lower()
                qty = ing.get("quantity", "")
                if name:
                    if name not in agg:
                        agg[name] = {"name": ing.get("name", name), "total_quantity": qty}
                    else:
                        agg[name]["total_quantity"] += f" + {qty}"

        # Simple categorisation
        categories: Dict[str, List] = {
            "Proteins": [], "Produce": [], "Grains": [],
            "Dairy & Eggs": [], "Other": []
        }
        protein_kw = {"chicken", "beef", "salmon", "fish", "tuna", "turkey", "tofu", "egg", "shrimp"}
        produce_kw = {"tomato", "spinach", "broccoli", "apple", "banana", "lemon", "garlic", "onion", "avocado", "pepper", "lettuce", "kale"}
        grain_kw = {"rice", "pasta", "bread", "oat", "quinoa", "flour", "tortilla", "wrap"}
        dairy_kw = {"milk", "yogurt", "cheese", "butter", "cream"}

        for name, item in agg.items():
            if any(k in name for k in protein_kw):
                categories["Proteins"].append(item)
            elif any(k in name for k in produce_kw):
                categories["Produce"].append(item)
            elif any(k in name for k in grain_kw):
                categories["Grains"].append(item)
            elif any(k in name for k in dairy_kw):
                categories["Dairy & Eggs"].append(item)
            else:
                categories["Other"].append(item)

        shopping_list = [
            {"category": cat, "items": items}
            for cat, items in categories.items()
            if items
        ]
        return {"meal_plan_id": meal_plan_id, "shopping_list": shopping_list}
