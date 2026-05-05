"""
ClairEat — Water Tracking Router
"""

from datetime import date, timedelta
from fastapi import APIRouter, Query

from app.core.logging import get_logger
from app.dependencies import DBDep, UserDep
from app.schemas.ai import WaterLogRequest, WaterTodayResponse, WaterHistoryResponse
from app.utils.nutrition_utils import water_target_ml
from datetime import datetime

logger = get_logger(__name__)
router = APIRouter(prefix="/water", tags=["Water Tracking"])


@router.post(
    "/log",
    response_model=WaterTodayResponse,
    summary="Log a water intake entry (ml)",
)
async def log_water(request: WaterLogRequest, user: UserDep, db: DBDep) -> WaterTodayResponse:
    today = str(date.today())
    await db.table("water_logs").insert({
        "user_id": user.id,
        "log_date": today,
        "amount_ml": request.amount_ml,
        "logged_at": datetime.utcnow().isoformat(),
    }).execute()
    return await _today_summary(user.id, db)


@router.get(
    "/today",
    response_model=WaterTodayResponse,
    summary="Today's hydration summary",
)
async def water_today(user: UserDep, db: DBDep) -> WaterTodayResponse:
    return await _today_summary(user.id, db)


@router.get(
    "/history",
    response_model=WaterHistoryResponse,
    summary="N-day water intake history",
)
async def water_history(
    days: int = Query(default=7, ge=1, le=90),
    user: UserDep = None,
    db: DBDep = None,
) -> WaterHistoryResponse:
    start = str(date.today() - timedelta(days=days - 1))
    resp = (
        await db.table("water_logs")
        .select("log_date, amount_ml")
        .eq("user_id", user.id)
        .gte("log_date", start)
        .order("log_date", desc=True)
        .execute()
    )
    profile = await _get_weight(user.id, db)
    target = water_target_ml(profile)

    by_date: dict = {}
    for row in resp.data or []:
        d = row["log_date"]
        by_date[d] = by_date.get(d, 0.0) + row["amount_ml"]

    history = [
        {"date": d, "total_ml": v, "target_ml": target, "glasses": round(v / 250, 1)}
        for d, v in sorted(by_date.items(), reverse=True)
    ]
    return WaterHistoryResponse(days=history)


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _today_summary(user_id: str, db) -> WaterTodayResponse:
    today = str(date.today())
    resp = (
        await db.table("water_logs")
        .select("amount_ml")
        .eq("user_id", user_id)
        .eq("log_date", today)
        .execute()
    )
    total = sum(r["amount_ml"] for r in (resp.data or []))
    weight = await _get_weight(user_id, db)
    target = water_target_ml(weight)
    return WaterTodayResponse(
        today_total_ml=total,
        target_ml=target,
        glasses_logged=round(total / 250, 1),
        pct_complete=round((total / target) * 100, 1) if target > 0 else 0,
    )


async def _get_weight(user_id: str, db) -> float:
    try:
        resp = await db.table("profiles").select("weight_kg").eq("id", user_id).single().execute()
        return float((resp.data or {}).get("weight_kg") or 70)
    except Exception:
        return 70.0
