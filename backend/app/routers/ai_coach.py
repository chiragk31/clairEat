"""
ClairEat — AI Coach Router
Streaming SSE chat, meal scoring, food swap, daily tip, day analysis.
"""

import json
from datetime import datetime

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.config import get_settings
from app.core.logging import get_logger
from app.core.rate_limiter import check_rate_limit
from app.dependencies import DBDep, UserDep
from app.schemas.ai import (
    ChatRequest,
    ChatHistoryResponse,
    DailyTipResponse,
    DayAnalysisResponse,
    FoodSwapRequest,
    FoodSwapResponse,
    MealScoreRequest,
    MealScoreResponse,
)
from app.services.ai.orchestrator import get_ai_orchestrator
from app.services.ai.prompt_builder import PromptBuilder
from app.services.ai.response_parser import (
    parse_day_analysis,
    parse_food_swap,
    parse_meal_score,
    parse_tip,
)
from app.services.meals.meal_service import MealService

logger = get_logger(__name__)
router = APIRouter(prefix="/ai", tags=["AI Coach"])


@router.post(
    "/chat",
    summary="Stream a message to the AI nutritional coach",
    description="Returns Server-Sent Events (SSE). Use EventSource on the client.",
    response_class=StreamingResponse,
)
async def chat_with_coach(request: ChatRequest, user: UserDep, db: DBDep):
    """Streaming AI chat with full user context injection."""
    settings = get_settings()
    await check_rate_limit(user.id, "ai_chat", settings.ai_chat_rate_limit, 3600)

    # Gather context concurrently
    import asyncio
    profile_task = db.table("profiles").select("*").eq("id", user.id).single().execute()
    history_task = _get_chat_history(user.id, request.session_id, db)
    summary_task = MealService(db).get_daily_summary(user.id)

    profile_resp, history, summary = await asyncio.gather(profile_task, history_task, summary_task)
    profile = profile_resp.data or {}

    user_context = PromptBuilder.build_user_context(profile, summary["totals"], [])
    messages = [
        *history,
        {"role": "user", "content": f"{user_context}\n\nUser: {request.message}"},
    ]

    # Ensure or generate a session_id
    session_id = request.session_id or _new_uuid()
    orchestrator = get_ai_orchestrator()
    provider = orchestrator.current_provider()

    async def event_stream():
        full_response = ""
        try:
            async for chunk in orchestrator.stream_chat(messages, PromptBuilder.SYSTEM_PROMPT):
                full_response += chunk
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"
            return

        # Persist conversation (non-blocking)
        import asyncio as aio
        aio.create_task(_persist_messages(user.id, session_id, request.message, full_response, provider, db))
        yield f"data: {json.dumps({'done': True, 'session_id': session_id})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get(
    "/chat/history",
    response_model=ChatHistoryResponse,
    summary="Get conversation history",
    description="With session_id: returns that session's messages. Without: returns session previews.",
)
async def chat_history(
    session_id: str | None = Query(default=None),
    user: UserDep = None,
    db: DBDep = None,
) -> ChatHistoryResponse:
    if session_id:
        resp = (
            await db.table("ai_conversations")
            .select("*")
            .eq("user_id", user.id)
            .eq("session_id", session_id)
            .order("created_at")
            .execute()
        )
        messages = [
            {"role": r["role"], "content": r["content"], "ai_provider": r.get("ai_provider"), "created_at": str(r.get("created_at", ""))}
            for r in (resp.data or [])
        ]
        return ChatHistoryResponse(messages=messages)
    else:
        # Return session previews
        resp = (
            await db.table("ai_conversations")
            .select("session_id, content, created_at, role")
            .eq("user_id", user.id)
            .eq("role", "user")
            .order("created_at", desc=True)
            .limit(20)
            .execute()
        )
        seen_sessions: set = set()
        sessions = []
        for row in resp.data or []:
            sid = row["session_id"]
            if sid not in seen_sessions:
                seen_sessions.add(sid)
                sessions.append({
                    "session_id": str(sid),
                    "started_at": str(row.get("created_at", "")),
                    "preview": (row.get("content") or "")[:80],
                    "message_count": 0,
                })
        return ChatHistoryResponse(sessions=sessions)


@router.post(
    "/meal-score",
    response_model=MealScoreResponse,
    summary="Score a meal with AI",
)
async def score_meal(request: MealScoreRequest, user: UserDep, db: DBDep) -> MealScoreResponse:
    profile_resp = await db.table("profiles").select("*").eq("id", user.id).single().execute()
    profile = profile_resp.data or {}
    user_context = PromptBuilder.build_user_context(profile, {}, [])
    prompt = PromptBuilder.meal_score_prompt(request.items, user_context)
    orchestrator = get_ai_orchestrator()
    raw = await orchestrator.generate_json(prompt)
    result = parse_meal_score(raw)
    return MealScoreResponse(**result)


@router.post(
    "/food-swap",
    response_model=FoodSwapResponse,
    summary="Get healthier food alternatives",
)
async def food_swap(request: FoodSwapRequest, user: UserDep, db: DBDep) -> FoodSwapResponse:
    profile_resp = await db.table("profiles").select("*").eq("id", user.id).single().execute()
    user_context = PromptBuilder.build_user_context(profile_resp.data or {}, {}, [])
    prompt = PromptBuilder.food_swap_prompt(request.food_name, request.reason, user_context)
    orchestrator = get_ai_orchestrator()
    raw = await orchestrator.generate_json(prompt)
    result = parse_food_swap(raw)
    return FoodSwapResponse(original=request.food_name, alternatives=result["alternatives"])


@router.get(
    "/daily-tip",
    response_model=DailyTipResponse,
    summary="Get today's personalised nutrition tip (cached 24h per user)",
)
async def daily_tip(user: UserDep, db: DBDep) -> DailyTipResponse:
    from app.core.cache import cache_manager
    cache_key = f"daily_tip:{user.id}:{datetime.utcnow().strftime('%Y-%m-%d')}"
    cached = await cache_manager.get_ai(cache_key)
    if cached:
        return DailyTipResponse(**cached)

    profile_resp = await db.table("profiles").select("*").eq("id", user.id).single().execute()
    user_context = PromptBuilder.build_user_context(profile_resp.data or {}, {}, [])
    prompt = PromptBuilder.daily_tip_prompt(user_context)
    orchestrator = get_ai_orchestrator()

    try:
        raw = await orchestrator.generate_json(prompt)
        result = parse_tip(raw)
    except Exception:
        result = {"tip": "Stay hydrated and aim for 8 glasses of water today!", "category": "hydration"}

    tip_data = {**result, "generated_at": datetime.utcnow().isoformat()}
    await cache_manager.set_ai(cache_key, tip_data)
    return DailyTipResponse(**tip_data)


@router.post(
    "/analyze-day",
    response_model=DayAnalysisResponse,
    summary="Full AI analysis of today's eating",
)
async def analyze_day(user: UserDep, db: DBDep) -> DayAnalysisResponse:
    import asyncio
    profile_task = db.table("profiles").select("*").eq("id", user.id).single().execute()
    meal_svc = MealService(db)
    today_task = meal_svc.get_today_meals(user.id)
    profile_resp, today_data = await asyncio.gather(profile_task, today_task)
    profile = profile_resp.data or {}
    today_meals = today_data.get("meals", [])
    summary_data = await meal_svc.get_daily_summary(user.id)
    user_context = PromptBuilder.build_user_context(profile, summary_data["totals"], [])
    prompt = PromptBuilder.day_analysis_prompt(user_context, today_meals)
    orchestrator = get_ai_orchestrator()
    raw = await orchestrator.generate_json(prompt)
    result = parse_day_analysis(raw)
    return DayAnalysisResponse(**result)


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_chat_history(user_id: str, session_id: str | None, db) -> list:
    if not session_id:
        return []
    resp = (
        await db.table("ai_conversations")
        .select("role, content")
        .eq("user_id", user_id)
        .eq("session_id", session_id)
        .order("created_at")
        .limit(20)
        .execute()
    )
    return [{"role": r["role"], "content": r["content"]} for r in (resp.data or [])]


async def _persist_messages(
    user_id: str, session_id: str, user_msg: str, ai_msg: str, provider: str, db
) -> None:
    now = datetime.utcnow().isoformat()
    rows = [
        {"user_id": user_id, "session_id": session_id, "role": "user",
         "content": user_msg, "ai_provider": None, "created_at": now},
        {"user_id": user_id, "session_id": session_id, "role": "assistant",
         "content": ai_msg, "ai_provider": provider, "created_at": now},
    ]
    try:
        await db.table("ai_conversations").insert(rows).execute()
    except Exception as exc:
        logger.warning("Failed to persist chat messages", error=str(exc))


def _new_uuid() -> str:
    import uuid
    return str(uuid.uuid4())
