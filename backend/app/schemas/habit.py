"""ClairEat — Habit & Streak Schemas"""

from typing import List, Optional
from pydantic import BaseModel, Field


VALID_HABIT_TYPES = {"water_intake", "meal_timing", "vegetable_serving", "sugar_limit", "custom"}
VALID_FREQUENCIES = {"daily", "weekly"}


class CreateHabitRequest(BaseModel):
    habit_name: str = Field(max_length=200)
    habit_type: str
    target_value: float = Field(gt=0)
    target_unit: str = Field(max_length=50)
    frequency: str = "daily"
    reminder_times: List[str] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "habit_name": "Drink 8 glasses of water",
                "habit_type": "water_intake",
                "target_value": 8,
                "target_unit": "glasses",
                "frequency": "daily",
                "reminder_times": ["08:00", "13:00", "19:00"],
            }
        }


class UpdateHabitRequest(BaseModel):
    habit_name: Optional[str] = Field(default=None, max_length=200)
    target_value: Optional[float] = Field(default=None, gt=0)
    target_unit: Optional[str] = Field(default=None, max_length=50)
    frequency: Optional[str] = None
    reminder_times: Optional[List[str]] = None
    is_active: Optional[bool] = None


class HabitResponse(BaseModel):
    id: str
    habit_name: str
    habit_type: str
    target_value: float
    target_unit: str
    frequency: str
    reminder_times: List[str]
    is_active: bool
    created_at: str


class LogHabitRequest(BaseModel):
    value_achieved: float = Field(ge=0)


class StreakData(BaseModel):
    current_streak: int
    longest_streak: int
    last_activity_date: Optional[str]


class LogHabitResponse(BaseModel):
    is_completed: bool
    value_achieved: float
    target_value: float
    streak: StreakData
    milestone_reached: Optional[str] = None


class HabitStreakResponse(BaseModel):
    habit_id: str
    habit_name: str
    streak: StreakData


class StreaksSummaryResponse(BaseModel):
    global_logging_streak: StreakData
    habits: List[HabitStreakResponse]


class SuggestedHabit(BaseModel):
    habit_name: str
    habit_type: str
    reason: str
    target_value: float
    target_unit: str


class SuggestedHabitsResponse(BaseModel):
    suggestions: List[SuggestedHabit]
