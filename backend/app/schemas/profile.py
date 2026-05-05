"""ClairEat — Profile & TDEE Schemas"""

from typing import List, Optional
from pydantic import BaseModel, Field, model_validator


VALID_GENDERS = {"male", "female", "other", "prefer_not_to_say"}
VALID_ACTIVITY = {"sedentary", "light", "moderate", "active", "very_active"}
VALID_GOALS = {"weight_loss", "muscle_gain", "maintenance", "diabetes_control", "aggressive_loss", "weight_gain"}
VALID_DIETARY = {"vegetarian", "vegan", "gluten_free", "lactose_free", "halal", "kosher"}


class OnboardingRequest(BaseModel):
    full_name: str = Field(max_length=120)
    age: int = Field(ge=13, le=120)
    gender: str
    height_cm: float = Field(gt=50, lt=300)
    weight_kg: float = Field(gt=20, lt=500)
    target_weight_kg: Optional[float] = Field(default=None, gt=20, lt=500)
    activity_level: str
    health_goals: List[str] = Field(default_factory=list)
    dietary_restrictions: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    timezone: str = "UTC"
    location_city: Optional[str] = None

    @model_validator(mode="after")
    def validate_enums(self) -> "OnboardingRequest":
        if self.gender not in VALID_GENDERS:
            raise ValueError(f"gender must be one of {VALID_GENDERS}")
        if self.activity_level not in VALID_ACTIVITY:
            raise ValueError(f"activity_level must be one of {VALID_ACTIVITY}")
        invalid_goals = set(self.health_goals) - VALID_GOALS
        if invalid_goals:
            raise ValueError(f"Invalid health goals: {invalid_goals}")
        return self


class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(default=None, max_length=120)
    age: Optional[int] = Field(default=None, ge=13, le=120)
    gender: Optional[str] = None
    height_cm: Optional[float] = Field(default=None, gt=50, lt=300)
    weight_kg: Optional[float] = Field(default=None, gt=20, lt=500)
    target_weight_kg: Optional[float] = Field(default=None, gt=20, lt=500)
    activity_level: Optional[str] = None
    health_goals: Optional[List[str]] = None
    dietary_restrictions: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    timezone: Optional[str] = None
    location_city: Optional[str] = None


class TDEEResult(BaseModel):
    bmr: float
    tdee: float
    goal_calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    formula: str = "mifflin_st_jeor"


class ProfileResponse(BaseModel):
    id: str
    username: Optional[str]
    full_name: Optional[str]
    age: Optional[int]
    gender: Optional[str]
    height_cm: Optional[float]
    weight_kg: Optional[float]
    target_weight_kg: Optional[float]
    activity_level: Optional[str]
    health_goals: List[str]
    dietary_restrictions: List[str]
    allergies: List[str]
    daily_calorie_target: Optional[int]
    daily_protein_target_g: Optional[float]
    daily_carb_target_g: Optional[float]
    daily_fat_target_g: Optional[float]
    timezone: str
    location_city: Optional[str]
    onboarding_complete: bool
    created_at: str
    updated_at: str


class OnboardingResponse(BaseModel):
    profile: ProfileResponse
    tdee: TDEEResult
