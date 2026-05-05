"""ClairEat — Meal Schemas"""

from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field


VALID_MEAL_TYPES = {"breakfast", "lunch", "dinner", "snack", "pre_workout", "post_workout"}
VALID_MOODS = {"happy", "stressed", "tired", "neutral", "energetic", "anxious"}


class MealLogItemRequest(BaseModel):
    """A single food entry within a meal log."""
    food_item_id: Optional[str] = None          # UUID of cached food_items row
    custom_food_name: Optional[str] = Field(default=None, max_length=200)
    quantity_g: float = Field(gt=0)
    # Required when food_item_id is absent (custom entry)
    calories: Optional[float] = Field(default=None, ge=0)
    protein_g: Optional[float] = Field(default=None, ge=0)
    carbs_g: Optional[float] = Field(default=None, ge=0)
    fat_g: Optional[float] = Field(default=None, ge=0)
    fiber_g: Optional[float] = Field(default=None, ge=0)


class LogMealRequest(BaseModel):
    meal_date: date
    meal_type: str
    items: List[MealLogItemRequest] = Field(min_length=1)
    mood_before: Optional[str] = None
    mood_after: Optional[str] = None
    hunger_level_before: Optional[int] = Field(default=None, ge=1, le=10)
    fullness_level_after: Optional[int] = Field(default=None, ge=1, le=10)
    location: Optional[str] = None
    notes: Optional[str] = Field(default=None, max_length=1000)


class MealLogItemResponse(BaseModel):
    id: str
    food_item_id: Optional[str]
    custom_food_name: Optional[str]
    quantity_g: float
    calories: float
    protein_g: Optional[float]
    carbs_g: Optional[float]
    fat_g: Optional[float]
    fiber_g: Optional[float]


class MealLogResponse(BaseModel):
    id: str
    meal_date: str
    meal_type: str
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    total_fiber_g: float
    mood_before: Optional[str]
    mood_after: Optional[str]
    hunger_level_before: Optional[int]
    fullness_level_after: Optional[int]
    notes: Optional[str]
    ai_meal_score: Optional[float]
    ai_feedback: Optional[str]
    image_url: Optional[str]
    logged_at: str
    items: List[MealLogItemResponse] = []


class LogMealResponse(BaseModel):
    meal_log_id: str
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    ai_meal_score: Optional[float] = None
    ai_feedback: Optional[str] = None


class TodayMealsResponse(BaseModel):
    date: str
    meals: List[MealLogResponse]


class DailySummaryResponse(BaseModel):
    date: str
    totals: dict
    targets: dict
    pct_complete: dict
    water_ml: float
    water_target_ml: float


class MealHistoryResponse(BaseModel):
    days: List[dict]
    total_days: int
