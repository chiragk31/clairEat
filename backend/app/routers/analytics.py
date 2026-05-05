"""
ClairEat — Analytics Router
Weekly reports, macro trends, goal progress, and nutrient gap analysis.
"""

from fastapi import APIRouter, Query
from typing import Optional

from app.dependencies import DBDep, UserDep
from app.services.analytics.report_service import ReportService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get(
    "/weekly",
    summary="7-day nutrition report",
    description="Aggregated macros grouped by day vs calorie target.",
)
async def weekly_report(
    week_start: Optional[str] = Query(default=None, description="ISO date YYYY-MM-DD (defaults to this Monday)"),
    user: UserDep = None,
    db: DBDep = None,
) -> dict:
    svc = ReportService(db)
    return await svc.weekly_report(user.id, week_start)


@router.get(
    "/trends",
    summary="Daily macro time-series (up to 90 days)",
)
async def macro_trends(
    days: int = Query(default=30, ge=7, le=90),
    user: UserDep = None,
    db: DBDep = None,
) -> dict:
    svc = ReportService(db)
    return await svc.trends(user.id, days)


@router.get(
    "/patterns",
    summary="Detected eating patterns (protein deficit, late nights, etc.)",
)
async def eating_patterns(user: UserDep, db: DBDep) -> dict:
    from app.services.analytics.report_service import PatternDetector
    detector = PatternDetector(db)
    patterns = await detector.detect_all(user.id)
    return {"patterns": patterns}


@router.get(
    "/goal-progress",
    summary="Progress toward health goals",
)
async def goal_progress(user: UserDep, db: DBDep) -> dict:
    svc = ReportService(db)
    return await svc.goal_progress(user.id)


@router.get(
    "/nutrient-gaps",
    summary="Chronically under-consumed micronutrients",
)
async def nutrient_gaps(user: UserDep, db: DBDep) -> dict:
    svc = ReportService(db)
    return await svc.nutrient_gaps(user.id)
