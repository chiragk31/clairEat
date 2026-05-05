"""
ClairEat — Meals Router
Log meals, retrieve meal history, daily summary, delete, and photo upload.
"""

import asyncio
from datetime import date

from fastapi import APIRouter, File, UploadFile

from app.core.exceptions import ValidationError
from app.core.logging import get_logger
from app.dependencies import DBDep, UserDep
from app.schemas.meal import (
    DailySummaryResponse,
    LogMealRequest,
    LogMealResponse,
    MealHistoryResponse,
    MealLogResponse,
    TodayMealsResponse,
)
from app.services.meals.meal_scorer import MealScorer
from app.services.meals.meal_service import MealService

logger = get_logger(__name__)
router = APIRouter(prefix="/meals", tags=["Meal Logging"])


@router.post(
    "/log",
    response_model=LogMealResponse,
    status_code=201,
    summary="Log a complete meal",
    description="Accepts one or more food items with quantities. AI scoring runs asynchronously.",
)
async def log_meal(request: LogMealRequest, user: UserDep, db: DBDep) -> LogMealResponse:
    """Log a meal and trigger async AI scoring."""
    if request.meal_type not in {
        "breakfast", "lunch", "dinner", "snack", "pre_workout", "post_workout"
    }:
        raise ValidationError(f"Invalid meal_type: {request.meal_type}")

    svc = MealService(db)
    result = await svc.log_meal(user.id, request)

    # Kick off async AI scoring (non-blocking)
    asyncio.create_task(
        _score_meal_async(db, user.id, result["meal_log_id"], request, result)
    )

    return LogMealResponse(**result)


@router.get(
    "/today",
    response_model=TodayMealsResponse,
    summary="Get all meals logged today",
)
async def get_today_meals(user: UserDep, db: DBDep) -> TodayMealsResponse:
    svc = MealService(db)
    data = await svc.get_today_meals(user.id)
    return TodayMealsResponse(date=data["date"], meals=data["meals"])


@router.get(
    "/daily-summary",
    response_model=DailySummaryResponse,
    summary="Aggregated macro totals vs targets for today",
)
async def daily_summary(user: UserDep, db: DBDep) -> DailySummaryResponse:
    svc = MealService(db)
    data = await svc.get_daily_summary(user.id)
    return DailySummaryResponse(**data)


@router.get(
    "/history",
    response_model=MealHistoryResponse,
    summary="N-day meal history grouped by date",
)
async def meal_history(
    days: int = 7, user: UserDep = None, db: DBDep = None
) -> MealHistoryResponse:
    days = max(1, min(days, 90))
    svc = MealService(db)
    data = await svc.get_meal_history(user.id, days)
    return MealHistoryResponse(**data)


@router.get(
    "/date/{meal_date}",
    response_model=TodayMealsResponse,
    summary="Get meals on a specific date (YYYY-MM-DD)",
)
async def meals_on_date(meal_date: str, user: UserDep, db: DBDep) -> TodayMealsResponse:
    try:
        date.fromisoformat(meal_date)
    except ValueError:
        raise ValidationError("Invalid date format. Use YYYY-MM-DD.")
    svc = MealService(db)
    data = await svc.get_meals_for_date(user.id, meal_date)
    return TodayMealsResponse(date=data["date"], meals=data["meals"])


@router.get(
    "/{meal_id}",
    response_model=MealLogResponse,
    summary="Get a single meal log with all items",
)
async def get_meal(meal_id: str, user: UserDep, db: DBDep) -> MealLogResponse:
    svc = MealService(db)
    data = await svc.get_meal_by_id(user.id, meal_id)
    return MealLogResponse(**_flatten_meal(data))


@router.delete(
    "/{meal_id}",
    status_code=204,
    summary="Delete a meal log",
)
async def delete_meal(meal_id: str, user: UserDep, db: DBDep) -> None:
    svc = MealService(db)
    await svc.delete_meal(user.id, meal_id)


@router.post(
    "/{meal_id}/photo",
    summary="Upload a meal photo",
    description="Accepts JPEG, PNG, or WebP. Max 5 MB. Stored in Supabase Storage.",
)
async def upload_meal_photo(
    meal_id: str,
    user: UserDep,
    db: DBDep,
    file: UploadFile = File(...),
) -> dict:
    from app.config import get_settings
    from app.core.exceptions import ValidationError as VError
    settings = get_settings()

    if file.content_type not in settings.allowed_image_types:
        raise VError(f"Unsupported file type: {file.content_type}. Use JPEG, PNG, or WebP.")

    contents = await file.read()
    if len(contents) > settings.max_upload_size_mb * 1024 * 1024:
        raise VError(f"File too large. Max size is {settings.max_upload_size_mb}MB.")

    path = f"meal-photos/{user.id}/{meal_id}.{file.content_type.split('/')[1]}"
    try:
        await db.storage.from_("meal-photos").upload(path, contents, {"content-type": file.content_type})
        public_url = db.storage.from_("meal-photos").get_public_url(path)
        await db.table("meal_logs").update({"image_url": public_url}).eq("id", meal_id).eq("user_id", user.id).execute()
        return {"image_url": public_url}
    except Exception as exc:
        from app.core.exceptions import StorageError
        raise StorageError(f"Photo upload failed: {exc}")


# ── Background Task ───────────────────────────────────────────────────────────

async def _score_meal_async(db, user_id: str, meal_log_id: str, request: LogMealRequest, totals: dict) -> None:
    """Run AI meal scoring in the background after meal is logged."""
    try:
        profile_resp = await db.table("profiles").select("*").eq("id", user_id).single().execute()
        profile = profile_resp.data or {}
        today_summary = {"calories": totals["total_calories"], "protein_g": totals["total_protein_g"],
                         "carbs_g": totals["total_carbs_g"], "fat_g": totals["total_fat_g"], "water_ml": 0}
        food_items = [
            {"name": item.custom_food_name or "Food item", "quantity_g": item.quantity_g,
             "calories": totals["total_calories"]}
            for item in request.items
        ]
        scorer = MealScorer()
        score_result = await scorer.score(food_items, profile, today_summary)
        svc = MealService(db)
        await svc.update_ai_score(meal_log_id, score_result["score"], score_result["feedback"])
    except Exception as exc:
        logger.warning("Async meal scoring failed", error=str(exc))


def _flatten_meal(data: dict) -> dict:
    return {
        "id": data.get("id", ""),
        "meal_date": str(data.get("meal_date", "")),
        "meal_type": data.get("meal_type", ""),
        "total_calories": float(data.get("total_calories") or 0),
        "total_protein_g": float(data.get("total_protein_g") or 0),
        "total_carbs_g": float(data.get("total_carbs_g") or 0),
        "total_fat_g": float(data.get("total_fat_g") or 0),
        "total_fiber_g": float(data.get("total_fiber_g") or 0),
        "mood_before": data.get("mood_before"),
        "mood_after": data.get("mood_after"),
        "hunger_level_before": data.get("hunger_level_before"),
        "fullness_level_after": data.get("fullness_level_after"),
        "notes": data.get("notes"),
        "ai_meal_score": data.get("ai_meal_score"),
        "ai_feedback": data.get("ai_feedback"),
        "image_url": data.get("image_url"),
        "logged_at": str(data.get("logged_at", "")),
        "items": data.get("meal_log_items") or [],
    }
