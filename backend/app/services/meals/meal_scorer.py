"""
ClairEat — Meal Scorer
Asynchronously scores a logged meal using the AI orchestrator.
"""

from typing import Any, Dict, List

from app.core.logging import get_logger
from app.services.ai.orchestrator import get_ai_orchestrator
from app.services.ai.prompt_builder import PromptBuilder
from app.services.ai.response_parser import parse_meal_score

logger = get_logger(__name__)


class MealScorer:
    """Scores a meal out of 100 using Gemini/Groq AI feedback."""

    async def score(
        self,
        food_items: List[Dict[str, Any]],
        user_profile: Dict[str, Any],
        today_summary: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate a meal quality score.

        Args:
            food_items:    List of food item dicts with name + nutrients.
            user_profile:  User's profile (goals, targets, restrictions).
            today_summary: Today's running macro totals.

        Returns:
            Dict with score (0-100), grade, feedback, suggestions.
        """
        user_context = PromptBuilder.build_user_context(
            profile=user_profile,
            today_summary=today_summary,
            recent_meals=[],
        )
        prompt = PromptBuilder.meal_score_prompt(food_items, user_context)
        orchestrator = get_ai_orchestrator()

        try:
            raw = await orchestrator.generate_json(prompt)
            result = parse_meal_score(raw)
            logger.info("Meal scored", score=result["score"])
            return result
        except Exception as exc:
            logger.warning("Meal scoring failed", error=str(exc))
            return {
                "score": 50,
                "grade": "C",
                "feedback": "Unable to generate AI feedback at this time.",
                "suggestions": [],
            }
