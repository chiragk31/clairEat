"""
ClairEat — Habit Service & Streak Engine
Habit CRUD, daily log recording, and streak calculation with milestone detection.
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from supabase import AsyncClient

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.schemas.habit import CreateHabitRequest, UpdateHabitRequest

logger = get_logger(__name__)

MILESTONES = [7, 14, 21, 30, 60, 90, 180, 365]


class HabitService:
    """Handles habit CRUD, daily logging, streak calculation."""

    def __init__(self, db: AsyncClient) -> None:
        self._db = db

    # ── CRUD ──────────────────────────────────────────────────────────────

    async def create_habit(self, user_id: str, req: CreateHabitRequest) -> Dict[str, Any]:
        row = {
            "user_id": user_id,
            "habit_name": req.habit_name,
            "habit_type": req.habit_type,
            "target_value": req.target_value,
            "target_unit": req.target_unit,
            "frequency": req.frequency,
            "reminder_times": req.reminder_times,
            "is_active": True,
            "created_at": datetime.utcnow().isoformat(),
        }
        resp = await self._db.table("habits").insert(row).execute()
        habit = resp.data[0]

        # Create initial streak record
        await self._db.table("streaks").insert({
            "user_id": user_id,
            "habit_id": habit["id"],
            "streak_type": "habit_specific",
            "current_streak": 0,
            "longest_streak": 0,
            "last_activity_date": None,
            "updated_at": datetime.utcnow().isoformat(),
        }).execute()

        return habit

    async def list_habits(self, user_id: str) -> List[Dict[str, Any]]:
        resp = (
            await self._db.table("habits")
            .select("*")
            .eq("user_id", user_id)
            .eq("is_active", True)
            .order("created_at")
            .execute()
        )
        return resp.data or []

    async def update_habit(
        self, user_id: str, habit_id: str, req: UpdateHabitRequest
    ) -> Dict[str, Any]:
        updates = req.model_dump(exclude_none=True)
        if not updates:
            return await self._get_habit(user_id, habit_id)
        resp = (
            await self._db.table("habits")
            .update(updates)
            .eq("id", habit_id)
            .eq("user_id", user_id)
            .execute()
        )
        if not resp.data:
            raise NotFoundError(f"Habit {habit_id} not found.")
        return resp.data[0]

    async def delete_habit(self, user_id: str, habit_id: str) -> None:
        """Soft-delete by setting is_active = false."""
        resp = (
            await self._db.table("habits")
            .update({"is_active": False})
            .eq("id", habit_id)
            .eq("user_id", user_id)
            .execute()
        )
        if not resp.data:
            raise NotFoundError(f"Habit {habit_id} not found.")

    # ── Logging ───────────────────────────────────────────────────────────

    async def log_habit(
        self, user_id: str, habit_id: str, value_achieved: float
    ) -> Dict[str, Any]:
        """Log today's value for a habit and update streak.

        Returns completion status, updated streak, and any milestone reached.
        """
        habit = await self._get_habit(user_id, habit_id)
        today = date.today()
        is_completed = value_achieved >= habit["target_value"]

        # Upsert today's habit log
        await self._db.table("habit_logs").upsert({
            "habit_id": habit_id,
            "user_id": user_id,
            "log_date": str(today),
            "value_achieved": value_achieved,
            "is_completed": is_completed,
            "logged_at": datetime.utcnow().isoformat(),
        }, on_conflict="habit_id,log_date").execute()

        # Update streak if completed
        streak_data, milestone = await self._update_streak(
            user_id, habit_id, today, is_completed
        )

        return {
            "is_completed": is_completed,
            "value_achieved": value_achieved,
            "target_value": habit["target_value"],
            "streak": streak_data,
            "milestone_reached": milestone,
        }

    async def get_habit_streak(self, user_id: str, habit_id: str) -> Dict[str, Any]:
        """Return streak data for a specific habit."""
        resp = (
            await self._db.table("streaks")
            .select("*")
            .eq("user_id", user_id)
            .eq("habit_id", habit_id)
            .single()
            .execute()
        )
        if not resp.data:
            return {"current_streak": 0, "longest_streak": 0, "last_activity_date": None}
        s = resp.data
        return {
            "current_streak": s["current_streak"],
            "longest_streak": s["longest_streak"],
            "last_activity_date": s.get("last_activity_date"),
        }

    async def get_streaks_summary(self, user_id: str) -> Dict[str, Any]:
        """Return all streaks including global logging streak."""
        # Global logging streak
        global_resp = (
            await self._db.table("streaks")
            .select("current_streak, longest_streak, last_activity_date")
            .eq("user_id", user_id)
            .eq("streak_type", "logging")
            .is_("habit_id", "null")
            .limit(1)
            .execute()
        )
        g = (global_resp.data or [{}])[0]
        global_streak = {
            "current": g.get("current_streak", 0),
            "longest": g.get("longest_streak", 0),
        }

        # Per-habit streaks
        habits = await self.list_habits(user_id)
        habit_streaks = []
        for habit in habits:
            s = await self.get_habit_streak(user_id, habit["id"])
            habit_streaks.append({
                "habit_id": habit["id"],
                "habit_name": habit["habit_name"],
                "streak": s,
            })

        return {
            "global_logging_streak": global_streak,
            "habits": habit_streaks,
        }

    # ── Private ───────────────────────────────────────────────────────────

    async def _get_habit(self, user_id: str, habit_id: str) -> Dict[str, Any]:
        resp = (
            await self._db.table("habits")
            .select("*")
            .eq("id", habit_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        if not resp.data:
            raise NotFoundError(f"Habit {habit_id} not found.")
        return resp.data

    async def _update_streak(
        self, user_id: str, habit_id: str, today: date, is_completed: bool
    ) -> tuple[Dict[str, Any], Optional[str]]:
        """Update streak counters and detect milestones."""
        resp = (
            await self._db.table("streaks")
            .select("*")
            .eq("habit_id", habit_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        streak = resp.data or {}
        yesterday = today - timedelta(days=1)
        last_raw = streak.get("last_activity_date")
        last_date = date.fromisoformat(last_raw) if last_raw else None

        current = streak.get("current_streak", 0)
        longest = streak.get("longest_streak", 0)

        if not is_completed:
            streak_data = {"current_streak": current, "longest_streak": longest, "last_activity_date": last_raw}
            return streak_data, None

        if last_date == today:
            # Already logged today
            streak_data = {"current_streak": current, "longest_streak": longest, "last_activity_date": str(today)}
            return streak_data, None
        elif last_date == yesterday:
            current += 1
        else:
            current = 1

        longest = max(current, longest)
        milestone = None
        if current in MILESTONES:
            milestone = f"{current}_days"
            logger.info("Streak milestone reached!", habit_id=habit_id, milestone=milestone)

        await self._db.table("streaks").update({
            "current_streak": current,
            "longest_streak": longest,
            "last_activity_date": str(today),
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("habit_id", habit_id).eq("user_id", user_id).execute()

        return {
            "current_streak": current,
            "longest_streak": longest,
            "last_activity_date": str(today),
        }, milestone
