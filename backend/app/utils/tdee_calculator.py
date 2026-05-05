"""
ClairEat — TDEE & Macro Calculator
Implements the Mifflin-St Jeor BMR formula and macro splitting logic.
"""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class TDEEResult:
    """Result of a TDEE + macro calculation."""
    bmr: float
    tdee: float
    goal_calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    formula: str = "mifflin_st_jeor"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bmr": self.bmr,
            "tdee": self.tdee,
            "goal_calories": self.goal_calories,
            "protein_g": self.protein_g,
            "carbs_g": self.carbs_g,
            "fat_g": self.fat_g,
            "formula": self.formula,
        }


class TDEECalculator:
    """Mifflin-St Jeor BMR + activity multiplier + goal adjustment.

    Formula:
        Male:   BMR = (10 × weight_kg) + (6.25 × height_cm) − (5 × age) + 5
        Female: BMR = (10 × weight_kg) + (6.25 × height_cm) − (5 × age) − 161
        Other:  Average of male/female
    """

    ACTIVITY_MULTIPLIERS: Dict[str, float] = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9,
    }

    GOAL_ADJUSTMENTS: Dict[str, int] = {
        "weight_loss": -500,
        "aggressive_loss": -750,
        "maintenance": 0,
        "muscle_gain": 300,
        "weight_gain": 500,
        "diabetes_control": -250,
    }

    MIN_SAFE_CALORIES = 1200.0

    @classmethod
    def calculate(
        cls,
        age: int,
        gender: str,
        weight_kg: float,
        height_cm: float,
        activity_level: str,
        health_goals: list[str],
    ) -> TDEEResult:
        """Calculate BMR, TDEE, goal-adjusted calories, and macro targets.

        Args:
            age:            User age in years.
            gender:         'male' | 'female' | 'other' | 'prefer_not_to_say'
            weight_kg:      Body weight in kilograms.
            height_cm:      Body height in centimetres.
            activity_level: One of the keys in ACTIVITY_MULTIPLIERS.
            health_goals:   Ordered list; first goal drives calorie adjustment.

        Returns:
            TDEEResult with rounded values.
        """
        # BMR
        if gender == "male":
            bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
        elif gender == "female":
            bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161
        else:
            # Average of both formulas for 'other' / 'prefer_not_to_say'
            bmr_m = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
            bmr_f = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161
            bmr = (bmr_m + bmr_f) / 2

        multiplier = cls.ACTIVITY_MULTIPLIERS.get(activity_level, 1.2)
        tdee = bmr * multiplier

        primary_goal = health_goals[0] if health_goals else "maintenance"
        adjustment = cls.GOAL_ADJUSTMENTS.get(primary_goal, 0)
        goal_calories = max(cls.MIN_SAFE_CALORIES, tdee + adjustment)

        # Macro split
        # Protein: 1.6 g/kg for active users (evidence-based)
        protein_g = weight_kg * 1.6
        # Fat:  25% of goal calories
        fat_g = (goal_calories * 0.25) / 9
        # Carbs: remainder
        carbs_g = (goal_calories - (protein_g * 4) - (fat_g * 9)) / 4
        carbs_g = max(carbs_g, 50.0)   # never below minimum carb floor

        return TDEEResult(
            bmr=round(bmr, 1),
            tdee=round(tdee, 1),
            goal_calories=round(goal_calories, 1),
            protein_g=round(protein_g, 1),
            carbs_g=round(carbs_g, 1),
            fat_g=round(fat_g, 1),
        )
