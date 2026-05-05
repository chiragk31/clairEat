"""
ClairEat — Habits & Streaks Router
CRUD for habits, daily logging, streak tracking, and AI-suggested habits.
"""

from fastapi import APIRouter

from app.core.logging import get_logger
from app.dependencies import DBDep, UserDep
from app.schemas.habit import (
    CreateHabitRequest,
    HabitResponse,
    HabitStreakResponse,
    LogHabitRequest,
    LogHabitResponse,
    SuggestedHabitsResponse,
    StreaksSummaryResponse,
    UpdateHabitRequest,
)
from app.services.habits.habit_service import HabitService

logger = get_logger(__name__)
router = APIRouter(tags=["Habits & Streaks"])


# ── Habits ────────────────────────────────────────────────────────────────────

@router.post(
    "/habits",
    response_model=HabitResponse,
    status_code=201,
    summary="Create a new habit",
)
async def create_habit(request: CreateHabitRequest, user: UserDep, db: DBDep) -> HabitResponse:
    svc = HabitService(db)
    habit = await svc.create_habit(user.id, request)
    return _to_habit_response(habit)


@router.get(
    "/habits",
    response_model=list[HabitResponse],
    summary="List all active habits",
)
async def list_habits(user: UserDep, db: DBDep) -> list[HabitResponse]:
    svc = HabitService(db)
    habits = await svc.list_habits(user.id)
    return [_to_habit_response(h) for h in habits]


@router.put(
    "/habits/{habit_id}",
    response_model=HabitResponse,
    summary="Update habit settings",
)
async def update_habit(
    habit_id: str, request: UpdateHabitRequest, user: UserDep, db: DBDep
) -> HabitResponse:
    svc = HabitService(db)
    habit = await svc.update_habit(user.id, habit_id, request)
    return _to_habit_response(habit)


@router.delete(
    "/habits/{habit_id}",
    status_code=204,
    summary="Archive a habit (soft-delete)",
)
async def delete_habit(habit_id: str, user: UserDep, db: DBDep) -> None:
    svc = HabitService(db)
    await svc.delete_habit(user.id, habit_id)


@router.post(
    "/habits/{habit_id}/log",
    response_model=LogHabitResponse,
    summary="Log today's value for a habit",
)
async def log_habit(
    habit_id: str, request: LogHabitRequest, user: UserDep, db: DBDep
) -> LogHabitResponse:
    svc = HabitService(db)
    result = await svc.log_habit(user.id, habit_id, request.value_achieved)
    return LogHabitResponse(**result)


@router.get(
    "/habits/{habit_id}/streak",
    response_model=HabitStreakResponse,
    summary="Get streak data for a specific habit",
)
async def get_habit_streak(habit_id: str, user: UserDep, db: DBDep) -> HabitStreakResponse:
    svc = HabitService(db)
    streak = await svc.get_habit_streak(user.id, habit_id)
    # Fetch habit name
    habit_resp = await db.table("habits").select("habit_name").eq("id", habit_id).single().execute()
    habit_name = (habit_resp.data or {}).get("habit_name", "")
    return HabitStreakResponse(
        habit_id=habit_id,
        habit_name=habit_name,
        streak=streak,
    )


@router.get(
    "/habits/suggested",
    response_model=SuggestedHabitsResponse,
    summary="AI-suggested habits based on your eating patterns",
)
async def suggested_habits(user: UserDep, db: DBDep) -> SuggestedHabitsResponse:
    """Analyse recent patterns and suggest personalised habits via AI."""
    from app.services.analytics.report_service import PatternDetector
    from app.services.ai.orchestrator import get_ai_orchestrator
    from app.services.ai.prompt_builder import PromptBuilder
    from app.services.ai.response_parser import parse_habit_suggestions

    profile_resp = await db.table("profiles").select("*").eq("id", user.id).single().execute()
    profile = profile_resp.data or {}
    today_resp = await db.table("meal_logs").select(
        "total_calories,total_protein_g,total_carbs_g,total_fat_g"
    ).eq("user_id", user.id).eq("meal_date", str(__import__("datetime").date.today())).execute()
    today_summary = {k: sum(r.get(k, 0) or 0 for r in (today_resp.data or []))
                     for k in ["total_calories", "total_protein_g", "total_carbs_g", "total_fat_g"]}

    detector = PatternDetector(db)
    patterns = await detector.detect_all(user.id)
    user_context = PromptBuilder.build_user_context(profile, today_summary, [])
    prompt = PromptBuilder.habit_suggestions_prompt(user_context, patterns)

    orchestrator = get_ai_orchestrator()
    try:
        raw = await orchestrator.generate_json(prompt)
        result = parse_habit_suggestions(raw)
        return SuggestedHabitsResponse(suggestions=result.get("suggestions", []))
    except Exception as exc:
        logger.warning("Habit suggestion failed", error=str(exc))
        return SuggestedHabitsResponse(suggestions=[])


# ── Streaks ───────────────────────────────────────────────────────────────────

@router.get(
    "/streaks/summary",
    response_model=StreaksSummaryResponse,
    summary="Summary of all streaks including global logging streak",
)
async def streaks_summary(user: UserDep, db: DBDep) -> StreaksSummaryResponse:
    svc = HabitService(db)
    data = await svc.get_streaks_summary(user.id)
    return StreaksSummaryResponse(
        global_logging_streak=data["global_logging_streak"],
        habits=data["habits"],
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _to_habit_response(data: dict) -> HabitResponse:
    return HabitResponse(
        id=data["id"],
        habit_name=data["habit_name"],
        habit_type=data["habit_type"],
        target_value=data["target_value"],
        target_unit=data["target_unit"],
        frequency=data["frequency"],
        reminder_times=data.get("reminder_times") or [],
        is_active=data.get("is_active", True),
        created_at=str(data.get("created_at", "")),
    )
