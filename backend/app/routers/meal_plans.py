"""
ClairEat — Meal Plans Router
AI-generated 7-day meal plans, activation, and shopping list.
"""

from fastapi import APIRouter

from app.config import get_settings
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.core.rate_limiter import check_rate_limit
from app.dependencies import DBDep, UserDep
from app.schemas.ai import GenerateMealPlanRequest, MealPlanResponse, ShoppingListResponse
from app.services.meals.meal_planner import MealPlanner
from app.services.meals.meal_service import MealService

logger = get_logger(__name__)
router = APIRouter(prefix="/meal-plans", tags=["Meal Plans"])


@router.post(
    "/generate",
    response_model=MealPlanResponse,
    status_code=201,
    summary="Generate a 7-day AI meal plan",
    description="Uses Gemini Flash (Groq fallback). Rate limited to 5 generations per user per day.",
)
async def generate_meal_plan(
    request: GenerateMealPlanRequest, user: UserDep, db: DBDep
) -> MealPlanResponse:
    settings = get_settings()
    await check_rate_limit(
        user.id, "meal_plan_generate", settings.meal_plan_rate_limit, 86400
    )
    # Load profile + today summary for context
    profile_resp = await db.table("profiles").select("*").eq("id", user.id).single().execute()
    profile = profile_resp.data or {}
    meal_svc = MealService(db)
    today_summary = await meal_svc.get_daily_summary(user.id)

    planner = MealPlanner(db)
    plan = await planner.generate(
        user_id=user.id,
        start_date=request.start_date,
        preferences=request.preferences.model_dump(),
        profile=profile,
        today_summary=today_summary["totals"],
    )
    logger.info("Meal plan generated", user_id=user.id, plan_id=plan["meal_plan_id"])
    return MealPlanResponse(**plan)


@router.get(
    "/active",
    response_model=MealPlanResponse,
    summary="Get current active meal plan",
)
async def get_active_plan(user: UserDep, db: DBDep) -> MealPlanResponse:
    resp = (
        await db.table("meal_plans")
        .select("*, meal_plan_entries(*)")
        .eq("user_id", user.id)
        .eq("is_active", True)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if not resp.data:
        raise NotFoundError("No active meal plan. Generate one first.")
    return _to_plan_response(resp.data[0])


@router.get(
    "/{plan_id}",
    response_model=MealPlanResponse,
    summary="Get a specific meal plan by ID",
)
async def get_meal_plan(plan_id: str, user: UserDep, db: DBDep) -> MealPlanResponse:
    resp = (
        await db.table("meal_plans")
        .select("*, meal_plan_entries(*)")
        .eq("id", plan_id)
        .eq("user_id", user.id)
        .single()
        .execute()
    )
    if not resp.data:
        raise NotFoundError(f"Meal plan {plan_id} not found.")
    return _to_plan_response(resp.data)


@router.post(
    "/{plan_id}/activate",
    summary="Set a meal plan as the active plan",
)
async def activate_plan(plan_id: str, user: UserDep, db: DBDep) -> dict:
    await db.table("meal_plans").update({"is_active": False}).eq("user_id", user.id).execute()
    resp = (
        await db.table("meal_plans")
        .update({"is_active": True})
        .eq("id", plan_id)
        .eq("user_id", user.id)
        .execute()
    )
    if not resp.data:
        raise NotFoundError(f"Meal plan {plan_id} not found.")
    return {"message": "Meal plan activated.", "meal_plan_id": plan_id}


@router.delete(
    "/{plan_id}",
    status_code=204,
    summary="Delete a meal plan",
)
async def delete_meal_plan(plan_id: str, user: UserDep, db: DBDep) -> None:
    resp = (
        await db.table("meal_plans")
        .delete()
        .eq("id", plan_id)
        .eq("user_id", user.id)
        .execute()
    )
    if not resp.data:
        raise NotFoundError(f"Meal plan {plan_id} not found.")


@router.get(
    "/{plan_id}/shopping",
    response_model=ShoppingListResponse,
    summary="Generate shopping list from a meal plan",
)
async def get_shopping_list(plan_id: str, user: UserDep, db: DBDep) -> ShoppingListResponse:
    planner = MealPlanner(db)
    result = await planner.get_shopping_list(plan_id, user.id)
    return ShoppingListResponse(**result)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _to_plan_response(data: dict) -> MealPlanResponse:
    entries = data.get("meal_plan_entries") or []
    # Group entries by day_of_week
    by_dow: dict = {}
    for e in entries:
        dow = e.get("day_of_week", 1)
        by_dow.setdefault(dow, []).append({
            "meal_type": e.get("meal_type", ""),
            "recipe_name": e.get("recipe_name", ""),
            "recipe_description": e.get("recipe_description"),
            "estimated_calories": e.get("estimated_calories", 0),
            "estimated_protein_g": e.get("estimated_protein_g", 0),
            "estimated_carbs_g": e.get("estimated_carbs_g", 0),
            "estimated_fat_g": e.get("estimated_fat_g", 0),
            "prep_time_minutes": e.get("prep_time_minutes"),
            "ingredients": e.get("ingredients") or [],
            "preparation_steps": e.get("preparation_steps") or [],
        })

    days_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    days = []
    start = data.get("start_date", "")
    from datetime import date, timedelta
    try:
        start_d = date.fromisoformat(start)
    except Exception:
        start_d = date.today()

    for dow in sorted(by_dow.keys()):
        meals = by_dow[dow]
        day_date = start_d + timedelta(days=dow - 1)
        days.append({
            "day": days_names[dow - 1] if 1 <= dow <= 7 else f"Day {dow}",
            "day_of_week": dow,
            "date": str(day_date),
            "meals": meals,
            "total_calories": sum(m.get("estimated_calories", 0) for m in meals),
        })

    return MealPlanResponse(
        meal_plan_id=data["id"],
        plan_name=data.get("plan_name", ""),
        start_date=str(data.get("start_date", "")),
        end_date=str(data.get("end_date", "")),
        target_calories=data.get("target_calories", 2000),
        generated_by=data.get("generated_by", "gemini"),
        days=days,
    )
