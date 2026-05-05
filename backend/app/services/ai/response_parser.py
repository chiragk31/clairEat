"""
ClairEat — AI Response Parser
Validates and cleans structured JSON responses from AI providers.
"""

import json
import re
from typing import Any, Dict, Optional

from app.core.exceptions import AIServiceError
from app.core.logging import get_logger

logger = get_logger(__name__)


def _extract_json(raw: str) -> str:
    """Strip markdown code fences and surrounding prose from an AI response."""
    # Remove ```json ... ``` or ``` ... ``` fences
    raw = re.sub(r"```(?:json)?\s*", "", raw)
    raw = raw.replace("```", "").strip()
    # Find the first { or [ and last matching bracket
    start = min(
        (raw.find("{") if "{" in raw else len(raw)),
        (raw.find("[") if "[" in raw else len(raw)),
    )
    if start == len(raw):
        return raw
    return raw[start:]


def parse_json_response(raw: str, context: str = "AI response") -> Dict[str, Any]:
    """Parse a JSON string from an AI model, stripping any markdown fences.

    Args:
        raw:     The raw string returned by the AI provider.
        context: Human-readable label used in error messages.

    Returns:
        Parsed dict.

    Raises:
        AIServiceError: If the response cannot be parsed as valid JSON.
    """
    cleaned = _extract_json(raw)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.error(
            "Failed to parse AI JSON response",
            context=context,
            raw_preview=raw[:300],
            error=str(exc),
        )
        raise AIServiceError(
            f"AI returned invalid JSON for {context}: {exc}"
        ) from exc


def parse_meal_score(raw: str) -> Dict[str, Any]:
    """Parse and validate a meal-score AI response."""
    data = parse_json_response(raw, "meal_score")
    score = int(data.get("score", 50))
    return {
        "score": max(0, min(100, score)),
        "grade": data.get("grade", "C"),
        "feedback": data.get("feedback", ""),
        "suggestions": data.get("suggestions", []),
    }


def parse_meal_plan(raw: str) -> Dict[str, Any]:
    """Parse and validate a 7-day meal plan AI response."""
    data = parse_json_response(raw, "meal_plan")
    days = data.get("days", [])
    if not days:
        raise AIServiceError("AI returned a meal plan with no days.")
    return data


def parse_tip(raw: str) -> Dict[str, str]:
    """Parse a daily tip AI response."""
    data = parse_json_response(raw, "daily_tip")
    return {
        "tip": data.get("tip", "Stay hydrated today!"),
        "category": data.get("category", "habit"),
    }


def parse_day_analysis(raw: str) -> Dict[str, Any]:
    """Parse a full day analysis AI response."""
    data = parse_json_response(raw, "day_analysis")
    return {
        "summary": data.get("summary", ""),
        "score": int(data.get("score", 50)),
        "highlights": data.get("highlights", []),
        "improvements": data.get("improvements", []),
        "tomorrow_suggestion": data.get("tomorrow_suggestion", ""),
    }


def parse_food_swap(raw: str) -> Dict[str, Any]:
    """Parse a food swap alternatives AI response."""
    data = parse_json_response(raw, "food_swap")
    return {"alternatives": data.get("alternatives", [])}


def parse_habit_suggestions(raw: str) -> Dict[str, Any]:
    """Parse AI habit suggestions."""
    data = parse_json_response(raw, "habit_suggestions")
    return {"suggestions": data.get("suggestions", [])}
