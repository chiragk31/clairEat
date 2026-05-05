"""
ClairEat — AI Insight Generator
Converts significant behavioral patterns into persisted ai_insights rows.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List

from supabase import AsyncClient

from app.core.logging import get_logger

logger = get_logger(__name__)


class InsightGenerator:
    """Converts detected patterns into ai_insights table entries."""

    def __init__(self, db: AsyncClient) -> None:
        self._db = db

    async def create_from_patterns(
        self, user_id: str, patterns: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Persist patterns with confidence ≥ 0.7 as AI insights.

        Deduplicates by checking if a same-type insight already exists and
        is still valid (valid_until hasn't passed).
        """
        created = []
        for pattern in patterns:
            if pattern.get("confidence", 0) < 0.7:
                continue
            if await self._already_exists(user_id, pattern["type"]):
                continue

            insight = {
                "user_id": user_id,
                "insight_type": "pattern_detected",
                "title": self._title(pattern),
                "content": pattern.get("message", ""),
                "data": {
                    "pattern_type": pattern["type"],
                    "confidence": pattern["confidence"],
                    "suggestion": pattern.get("suggestion", ""),
                },
                "is_read": False,
                "valid_until": (datetime.utcnow() + timedelta(days=7)).isoformat(),
                "created_at": datetime.utcnow().isoformat(),
            }
            resp = await self._db.table("ai_insights").insert(insight).execute()
            if resp.data:
                created.append(resp.data[0])

        logger.info("Insights generated", count=len(created), user_id=user_id)
        return created

    async def get_user_insights(
        self, user_id: str, unread_only: bool = False, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Retrieve insights for a user, optionally filtering to unread only."""
        query = (
            self._db.table("ai_insights")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
        )
        if unread_only:
            query = query.eq("is_read", False)
        resp = await query.execute()
        return resp.data or []

    async def mark_read(self, user_id: str, insight_id: str) -> None:
        """Mark an insight as read."""
        await self._db.table("ai_insights").update({"is_read": True}).eq(
            "id", insight_id
        ).eq("user_id", user_id).execute()

    # ── Private ───────────────────────────────────────────────────────────

    async def _already_exists(self, user_id: str, pattern_type: str) -> bool:
        """Check if a valid insight of this type already exists."""
        now = datetime.utcnow().isoformat()
        resp = (
            await self._db.table("ai_insights")
            .select("id")
            .eq("user_id", user_id)
            .eq("insight_type", "pattern_detected")
            .contains("data", {"pattern_type": pattern_type})
            .gte("valid_until", now)
            .limit(1)
            .execute()
        )
        return bool(resp.data)

    @staticmethod
    def _title(pattern: Dict[str, Any]) -> str:
        titles = {
            "protein_deficit": "⚡ Low Protein Intake Detected",
            "breakfast_skipping": "🌅 Frequent Breakfast Skipping",
            "late_night_eating": "🌙 Late-Night Eating Pattern",
            "weekend_eating_difference": "📅 Weekend vs Weekday Eating Gap",
        }
        return titles.get(pattern["type"], "Nutrition Pattern Detected")
