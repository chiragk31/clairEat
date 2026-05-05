"""
ClairEat — Context-Aware AI Prompt Builder
Constructs rich, user-personalised prompts for all AI features.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional


class PromptBuilder:
    """Builds structured prompt strings for every AI use-case.

    Separates system instructions from dynamic user context so that
    caching at the system level stays valid across requests.
    """

    SYSTEM_PROMPT = (
        "You are ClairEat, an expert nutritionist and behavioral health coach. "
        "You help users make better food choices by combining evidence-based nutrition science "
        "with behavioural psychology. Always be encouraging, practical, and concise. "
        "Never give medical diagnoses. If a query is clearly medical, recommend consulting a doctor. "
        "Keep responses under 300 words unless the user explicitly asks for detail."
    )

    # ── Context Builder ───────────────────────────────────────────────────

    @staticmethod
    def build_user_context(
        profile: Dict[str, Any],
        today_summary: Dict[str, Any],
        recent_meals: List[Dict[str, Any]],
        weather: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Build a rich contextual string injected into every AI request."""
        now_str = datetime.now().strftime("%A %I:%M %p")

        recent_foods = []
        for meal in recent_meals[-5:]:
            if meal.get("items"):
                for item in meal["items"][:3]:
                    name = item.get("custom_food_name") or item.get("food_name", "Unknown")
                    recent_foods.append(name)
        recent_str = ", ".join(recent_foods) if recent_foods else "No recent meals logged"

        weather_str = ""
        if weather:
            weather_str = (
                f"\nWEATHER: {weather.get('condition', 'unknown')}, "
                f"{weather.get('temp_c', '?')}°C — factor this into suggestions."
            )

        return f"""
USER PROFILE:
- Age: {profile.get('age', '?')}, Gender: {profile.get('gender', '?')}
- Weight: {profile.get('weight_kg', '?')}kg, Height: {profile.get('height_cm', '?')}cm
- Activity Level: {profile.get('activity_level', '?')}
- Health Goals: {', '.join(profile.get('health_goals') or ['not set'])}
- Dietary Restrictions: {', '.join(profile.get('dietary_restrictions') or ['none'])}
- Allergies: {', '.join(profile.get('allergies') or ['none'])}
- Daily Calorie Target: {profile.get('daily_calorie_target', '?')} kcal
- Protein Target: {profile.get('daily_protein_target_g', '?')}g

TODAY SO FAR ({now_str}):
- Calories: {today_summary.get('calories', 0)} / {profile.get('daily_calorie_target', '?')} kcal
- Protein:  {today_summary.get('protein_g', 0)}g / {profile.get('daily_protein_target_g', '?')}g
- Carbs:    {today_summary.get('carbs_g', 0)}g
- Fat:      {today_summary.get('fat_g', 0)}g
- Water:    {today_summary.get('water_ml', 0)}ml

RECENT FOODS (last 5 items): {recent_str}
{weather_str}
""".strip()

    # ── Use-Case Prompts ──────────────────────────────────────────────────

    @staticmethod
    def meal_score_prompt(food_items: List[Dict], user_context: str) -> str:
        return f"""Score this meal out of 100 for the user below. Evaluate:
1. Alignment with their health goals
2. Macronutrient balance
3. Micronutrient density
4. Food processing level (NOVA group)

Return ONLY valid JSON:
{{"score": <int 0-100>, "grade": "<A|B|C|D|F>", "feedback": "<2-3 sentences>", "suggestions": ["<suggestion 1>", "<suggestion 2>"]}}

{user_context}

MEAL ITEMS:
{json.dumps(food_items, indent=2)}"""

    @staticmethod
    def food_swap_prompt(food_name: str, reason: str, user_context: str) -> str:
        return f"""Suggest 3 healthier alternatives to "{food_name}".
Reason for swap: {reason}

Return ONLY valid JSON:
{{"alternatives": [{{"name": "<food>", "benefit": "<why it's better>", "calories_per_100g": <optional int>}}]}}

{user_context}"""

    @staticmethod
    def daily_tip_prompt(user_context: str) -> str:
        return f"""Generate one personalised, actionable nutrition tip for this user today.
Return ONLY valid JSON:
{{"tip": "<one sentence tip>", "category": "<habit|nutrition|hydration|sleep|exercise>"}}

{user_context}"""

    @staticmethod
    def day_analysis_prompt(user_context: str, today_meals: List[Dict]) -> str:
        return f"""Analyse this user's eating for today and give a comprehensive report.
Return ONLY valid JSON:
{{
  "summary": "<2-3 sentence overview>",
  "score": <int 0-100>,
  "highlights": ["<positive point 1>", "<positive point 2>"],
  "improvements": ["<improvement 1>", "<improvement 2>"],
  "tomorrow_suggestion": "<one actionable recommendation for tomorrow>"
}}

{user_context}

TODAY'S MEALS:
{json.dumps(today_meals, indent=2)}"""

    @staticmethod
    def meal_plan_prompt(user_context: str, preferences: Dict[str, Any]) -> str:
        exclude = preferences.get("exclude_ingredients", [])
        cuisine = preferences.get("cuisine_preference", [])
        max_prep = preferences.get("max_prep_minutes", 45)
        return f"""Generate a 7-day personalised meal plan. Requirements:
- Each day: breakfast, lunch, dinner, 1-2 snacks
- Hit daily calorie target (±10%), respect dietary restrictions and allergies
- Exclude ingredients: {exclude or 'none'}
- Cuisine preference: {cuisine or 'any'}
- Max prep time per meal: {max_prep} minutes
- Vary meals daily, no repetition within 3 days

Return ONLY valid JSON matching this schema exactly:
{{
  "days": [
    {{
      "day": "<Monday|Tuesday|...>",
      "day_of_week": <1-7>,
      "meals": [
        {{
          "meal_type": "<breakfast|lunch|dinner|snack>",
          "recipe_name": "<name>",
          "recipe_description": "<1 sentence>",
          "estimated_calories": <int>,
          "estimated_protein_g": <float>,
          "estimated_carbs_g": <float>,
          "estimated_fat_g": <float>,
          "prep_time_minutes": <int>,
          "ingredients": [{{"name": "<ingredient>", "quantity": "<amount>"}}],
          "preparation_steps": ["<step 1>", "<step 2>"]
        }}
      ]
    }}
  ]
}}

{user_context}"""

    @staticmethod
    def habit_suggestions_prompt(user_context: str, patterns: List[Dict]) -> str:
        return f"""Based on this user's profile and detected eating patterns, suggest 3 specific habits.
Return ONLY valid JSON:
{{"suggestions": [{{"habit_name": "<name>", "habit_type": "<water_intake|meal_timing|vegetable_serving|sugar_limit|custom>", "reason": "<why this helps them>", "target_value": <number>, "target_unit": "<unit>"}}]}}

{user_context}

DETECTED PATTERNS:
{json.dumps(patterns, indent=2)}"""
