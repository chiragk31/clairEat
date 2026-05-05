"""
ClairEat — Analytics Report Service & Pattern Detector
Aggregated nutrition reports and behavioral pattern analysis.
"""

import asyncio
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from supabase import AsyncClient

from app.core.logging import get_logger

logger = get_logger(__name__)


class ReportService:
    """Generates nutrition aggregation reports."""

    def __init__(self, db: AsyncClient) -> None:
        self._db = db

    async def weekly_report(self, user_id: str, week_start: Optional[str] = None) -> Dict[str, Any]:
        """7-day macro aggregation report."""
        start = date.fromisoformat(week_start) if week_start else self._monday()
        end = start + timedelta(days=6)

        resp = (
            await self._db.table("meal_logs")
            .select("meal_date, total_calories, total_protein_g, total_carbs_g, total_fat_g")
            .eq("user_id", user_id)
            .gte("meal_date", str(start))
            .lte("meal_date", str(end))
            .order("meal_date")
            .execute()
        )

        # Group by date
        by_date: Dict[str, Dict] = {}
        for row in resp.data or []:
            d = row["meal_date"]
            if d not in by_date:
                by_date[d] = {"date": d, "calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0}
            by_date[d]["calories"] += row.get("total_calories") or 0
            by_date[d]["protein_g"] += row.get("total_protein_g") or 0
            by_date[d]["carbs_g"] += row.get("total_carbs_g") or 0
            by_date[d]["fat_g"] += row.get("total_fat_g") or 0

        days = list(by_date.values())
        avg_cal = sum(d["calories"] for d in days) / len(days) if days else 0

        # Profile for target
        profile_resp = await self._db.table("profiles").select("daily_calorie_target").eq("id", user_id).single().execute()
        calorie_target = (profile_resp.data or {}).get("daily_calorie_target", 2000)
        goal_hit_days = sum(1 for d in days if d["calories"] >= calorie_target * 0.9)

        return {
            "week": f"{start.strftime('%b %d')}–{end.strftime('%d %Y')}",
            "avg_daily_calories": round(avg_cal, 1),
            "calorie_target": calorie_target,
            "days": days,
            "goal_hit_days": goal_hit_days,
        }

    async def trends(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Daily macro time-series for the past N days."""
        start = date.today() - timedelta(days=days - 1)
        resp = (
            await self._db.table("meal_logs")
            .select("meal_date, total_calories, total_protein_g, total_carbs_g, total_fat_g")
            .eq("user_id", user_id)
            .gte("meal_date", str(start))
            .order("meal_date")
            .execute()
        )
        by_date: Dict[str, Dict] = {}
        for row in resp.data or []:
            d = row["meal_date"]
            if d not in by_date:
                by_date[d] = {"date": d, "calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0}
            by_date[d]["calories"] += row.get("total_calories") or 0
            by_date[d]["protein_g"] += row.get("total_protein_g") or 0
            by_date[d]["carbs_g"] += row.get("total_carbs_g") or 0
            by_date[d]["fat_g"] += row.get("total_fat_g") or 0

        return {"days": list(by_date.values()), "total_days": days}

    async def goal_progress(self, user_id: str) -> Dict[str, Any]:
        """Progress toward health goals over the past 14 days."""
        profile_resp = await self._db.table("profiles").select(
            "health_goals, daily_protein_target_g, daily_calorie_target, weight_kg, target_weight_kg"
        ).eq("id", user_id).single().execute()
        profile = profile_resp.data or {}

        start = date.today() - timedelta(days=13)
        resp = (
            await self._db.table("meal_logs")
            .select("total_calories, total_protein_g")
            .eq("user_id", user_id)
            .gte("meal_date", str(start))
            .execute()
        )
        logs = resp.data or []
        avg_cal = sum(r.get("total_calories") or 0 for r in logs) / len(logs) if logs else 0
        avg_pro = sum(r.get("total_protein_g") or 0 for r in logs) / len(logs) if logs else 0

        goals = []
        for goal in (profile.get("health_goals") or []):
            if goal in ("muscle_gain", "weight_gain"):
                pro_target = profile.get("daily_protein_target_g") or 100
                pct = min(int((avg_pro / pro_target) * 100), 100)
                goals.append({
                    "goal": goal,
                    "protein_avg_g": round(avg_pro, 1),
                    "protein_target_g": pro_target,
                    "pct_achieved": pct,
                    "on_track": pct >= 85,
                })
            elif goal in ("weight_loss", "aggressive_loss"):
                cal_target = profile.get("daily_calorie_target") or 1800
                pct = min(int((cal_target / avg_cal) * 100), 100) if avg_cal > 0 else 0
                goals.append({
                    "goal": goal,
                    "avg_calories": round(avg_cal, 1),
                    "calorie_target": cal_target,
                    "pct_achieved": pct,
                    "on_track": avg_cal <= cal_target * 1.05,
                })
        return {"goals": goals}

    async def nutrient_gaps(self, user_id: str) -> Dict[str, Any]:
        """Identify chronically under-consumed micronutrients over last 7 days."""
        # We look at food_items vitamins/minerals joined via meal_log_items
        # As a practical approach, we surface common gap targets
        TARGETS = {
            "vitamin_d": {"target": 15, "unit": "mcg"},
            "vitamin_c": {"target": 90, "unit": "mg"},
            "iron": {"target": 18, "unit": "mg"},
            "calcium": {"target": 1000, "unit": "mg"},
        }

        start = date.today() - timedelta(days=6)
        resp = (
            await self._db.table("meal_log_items")
            .select("quantity_g, food_items(vitamins, minerals)")
            .eq("meal_logs.user_id", user_id)
            .gte("meal_logs.meal_date", str(start))
            .execute()
        )

        totals: Dict[str, float] = {k: 0.0 for k in TARGETS}
        days_counted = 7

        for item in resp.data or []:
            fi = item.get("food_items") or {}
            qty = item.get("quantity_g") or 100
            for nutrient in TARGETS:
                val = (fi.get("vitamins") or {}).get(nutrient) or (fi.get("minerals") or {}).get(nutrient) or 0
                totals[nutrient] += (val * qty) / 100

        gaps = []
        for nutrient, meta in TARGETS.items():
            avg_intake = round(totals[nutrient] / days_counted, 2)
            target = meta["target"]
            gap_pct = max(0, int((1 - avg_intake / target) * 100)) if target > 0 else 0
            if gap_pct > 20:  # Only surface meaningful gaps
                gaps.append({
                    "nutrient": nutrient.replace("_", " ").title(),
                    "avg_intake": avg_intake,
                    "target": target,
                    "unit": meta["unit"],
                    "gap_pct": gap_pct,
                })

        return {"gaps": sorted(gaps, key=lambda x: x["gap_pct"], reverse=True)}

    @staticmethod
    def _monday() -> date:
        today = date.today()
        return today - timedelta(days=today.weekday())


class PatternDetector:
    """Detects behavioural eating patterns from meal log history.

    Patterns detected:
    - Protein deficit (>60% of days under target)
    - Meal skipping (breakfast skipped frequently)
    - Late-night eating (meals after 21:00)
    - Weekend vs weekday eating differences
    """

    def __init__(self, db: AsyncClient) -> None:
        self._db = db

    async def detect_all(self, user_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Run all pattern detectors and return significant patterns."""
        start = date.today() - timedelta(days=days)
        resp = (
            await self._db.table("meal_logs")
            .select("meal_date, meal_type, total_calories, total_protein_g, logged_at")
            .eq("user_id", user_id)
            .gte("meal_date", str(start))
            .execute()
        )
        logs = resp.data or []
        if len(logs) < 5:
            return []

        profile_resp = await self._db.table("profiles").select(
            "daily_protein_target_g"
        ).eq("id", user_id).single().execute()
        protein_target = float((profile_resp.data or {}).get("daily_protein_target_g") or 100)

        patterns = await asyncio.gather(
            self._detect_protein_deficit(logs, protein_target),
            self._detect_breakfast_skipping(logs),
            self._detect_late_night_eating(logs),
            self._detect_weekend_differences(logs),
        )
        return [p for p in patterns if p is not None]

    async def _detect_protein_deficit(
        self, logs: List[Dict], target: float
    ) -> Optional[Dict[str, Any]]:
        by_date: Dict[str, float] = {}
        for log in logs:
            d = log["meal_date"]
            by_date[d] = by_date.get(d, 0.0) + (log.get("total_protein_g") or 0)

        deficit_days = [d for d, val in by_date.items() if val < target * 0.8]
        if not by_date:
            return None
        confidence = len(deficit_days) / len(by_date)
        if confidence < 0.6:
            return None
        return {
            "type": "protein_deficit",
            "confidence": round(confidence, 2),
            "message": f"You're under your protein target on {len(deficit_days)} of the last {len(by_date)} days.",
            "suggestion": "Try adding a protein-rich snack like Greek yogurt or boiled eggs.",
        }

    async def _detect_breakfast_skipping(self, logs: List[Dict]) -> Optional[Dict[str, Any]]:
        by_date: Dict[str, List[str]] = {}
        for log in logs:
            by_date.setdefault(log["meal_date"], []).append(log.get("meal_type", ""))

        total_days = len(by_date)
        skip_days = sum(1 for meals in by_date.values() if "breakfast" not in meals)
        confidence = skip_days / total_days if total_days else 0
        if confidence < 0.5:
            return None
        return {
            "type": "breakfast_skipping",
            "confidence": round(confidence, 2),
            "message": f"You skipped breakfast on {skip_days} of the last {total_days} logged days.",
            "suggestion": "A protein-rich breakfast can reduce cravings and improve energy all morning.",
        }

    async def _detect_late_night_eating(self, logs: List[Dict]) -> Optional[Dict[str, Any]]:
        late_night = 0
        for log in logs:
            try:
                ts = log.get("logged_at") or ""
                hour = int(ts[11:13]) if len(ts) >= 13 else 0
                if hour >= 21:
                    late_night += 1
            except (ValueError, IndexError):
                continue
        confidence = late_night / len(logs) if logs else 0
        if confidence < 0.3:
            return None
        return {
            "type": "late_night_eating",
            "confidence": round(confidence, 2),
            "message": f"About {int(confidence * 100)}% of your meals are logged after 9 PM.",
            "suggestion": "Late-night calories are often extra. Try moving dinner earlier by 1 hour.",
        }

    async def _detect_weekend_differences(self, logs: List[Dict]) -> Optional[Dict[str, Any]]:
        weekday_cal: List[float] = []
        weekend_cal: Dict[str, float] = {}
        for log in logs:
            try:
                d = date.fromisoformat(log["meal_date"])
                cal = log.get("total_calories") or 0
                if d.weekday() < 5:
                    weekday_cal.append(float(cal))
                else:
                    key = str(d)
                    weekend_cal[key] = weekend_cal.get(key, 0.0) + float(cal)
            except Exception:
                continue

        if not weekday_cal or not weekend_cal:
            return None
        avg_weekday = sum(weekday_cal) / len(weekday_cal)
        avg_weekend = sum(weekend_cal.values()) / len(weekend_cal)
        diff_pct = abs(avg_weekend - avg_weekday) / avg_weekday if avg_weekday > 0 else 0

        if diff_pct < 0.2:
            return None
        direction = "higher" if avg_weekend > avg_weekday else "lower"
        return {
            "type": "weekend_eating_difference",
            "confidence": round(min(diff_pct, 1.0), 2),
            "message": f"Your weekend calorie intake is {int(diff_pct * 100)}% {direction} than weekdays.",
            "suggestion": "Keep weekend meals close to your weekday patterns for consistent progress.",
        }
