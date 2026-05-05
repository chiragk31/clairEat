"""
ClairEat — Insights Router
Retrieve and mark-as-read AI-generated insights.
"""

from fastapi import APIRouter, Query

from app.dependencies import DBDep, UserDep
from app.schemas.ai import InsightsListResponse
from app.services.analytics.insight_generator import InsightGenerator
from app.services.analytics.report_service import PatternDetector

router = APIRouter(prefix="/insights", tags=["Insights"])


@router.get(
    "",
    response_model=InsightsListResponse,
    summary="Get AI insights",
    description="Returns all insights, optionally filtered to unread only. "
                "Also triggers pattern detection to generate fresh insights.",
)
async def get_insights(
    unread_only: bool = Query(default=False),
    user: UserDep = None,
    db: DBDep = None,
) -> InsightsListResponse:
    # Run pattern detection to surface any new insights
    detector = PatternDetector(db)
    patterns = await detector.detect_all(user.id)
    generator = InsightGenerator(db)
    await generator.create_from_patterns(user.id, patterns)

    insights = await generator.get_user_insights(user.id, unread_only=unread_only)
    return InsightsListResponse(
        insights=[_to_insight(i) for i in insights],
        total=len(insights),
    )


@router.post(
    "/{insight_id}/read",
    status_code=204,
    summary="Mark an insight as read",
)
async def mark_insight_read(insight_id: str, user: UserDep, db: DBDep) -> None:
    generator = InsightGenerator(db)
    await generator.mark_read(user.id, insight_id)


def _to_insight(data: dict) -> dict:
    return {
        "id": data["id"],
        "insight_type": data.get("insight_type", ""),
        "title": data.get("title", ""),
        "content": data.get("content", ""),
        "data": data.get("data"),
        "is_read": data.get("is_read", False),
        "valid_until": str(data.get("valid_until") or ""),
        "created_at": str(data.get("created_at", "")),
    }
