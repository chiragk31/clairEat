"""ClairEat — AI Coach Schemas"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: Optional[str] = None   # None = start new session
    message: str = Field(min_length=1, max_length=4000)


class ChatHistoryEntry(BaseModel):
    role: str                # "user" | "assistant"
    content: str
    ai_provider: Optional[str] = None
    created_at: str


class SessionPreview(BaseModel):
    session_id: str
    started_at: str
    preview: str
    message_count: int


class ChatHistoryResponse(BaseModel):
    sessions: List[SessionPreview] = []
    messages: List[ChatHistoryEntry] = []


class MealScoreRequest(BaseModel):
    items: List[Dict[str, Any]] = Field(min_length=1)


class MealScoreResponse(BaseModel):
    score: int = Field(ge=0, le=100)
    grade: str
    feedback: str
    suggestions: List[str]


class FoodSwapRequest(BaseModel):
    food_name: str = Field(max_length=200)
    reason: str = Field(max_length=200)


class FoodAlternative(BaseModel):
    name: str
    benefit: str
    calories_per_100g: Optional[float] = None


class FoodSwapResponse(BaseModel):
    original: str
    alternatives: List[FoodAlternative]


class DailyTipResponse(BaseModel):
    tip: str
    category: str
    generated_at: str


class DayAnalysisResponse(BaseModel):
    summary: str
    score: int
    highlights: List[str]
    improvements: List[str]
    tomorrow_suggestion: str


class MealPlanPreference(BaseModel):
    exclude_ingredients: List[str] = Field(default_factory=list)
    cuisine_preference: List[str] = Field(default_factory=list)
    max_prep_minutes: Optional[int] = Field(default=None, ge=5, le=240)


class GenerateMealPlanRequest(BaseModel):
    start_date: str          # ISO date: YYYY-MM-DD
    preferences: MealPlanPreference = Field(default_factory=MealPlanPreference)


class MealPlanEntry(BaseModel):
    meal_type: str
    recipe_name: str
    recipe_description: Optional[str] = None
    estimated_calories: int
    estimated_protein_g: float
    estimated_carbs_g: float
    estimated_fat_g: float
    prep_time_minutes: Optional[int] = None
    ingredients: List[Dict[str, str]] = []
    preparation_steps: List[str] = []


class MealPlanDay(BaseModel):
    day: str
    day_of_week: int
    date: str
    meals: List[MealPlanEntry]
    total_calories: int


class MealPlanResponse(BaseModel):
    meal_plan_id: str
    plan_name: str
    start_date: str
    end_date: str
    target_calories: int
    generated_by: str
    days: List[MealPlanDay]


class ShoppingItem(BaseModel):
    name: str
    total_quantity: str


class ShoppingCategory(BaseModel):
    category: str
    items: List[ShoppingItem]


class ShoppingListResponse(BaseModel):
    meal_plan_id: str
    shopping_list: List[ShoppingCategory]


class InsightResponse(BaseModel):
    id: str
    insight_type: str
    title: str
    content: str
    data: Optional[Dict[str, Any]] = None
    is_read: bool
    valid_until: Optional[str] = None
    created_at: str


class InsightsListResponse(BaseModel):
    insights: List[InsightResponse]
    total: int


class WaterLogRequest(BaseModel):
    amount_ml: int = Field(gt=0, le=2000)


class WaterTodayResponse(BaseModel):
    today_total_ml: float
    target_ml: float
    glasses_logged: float
    pct_complete: float


class WaterHistoryDay(BaseModel):
    date: str
    total_ml: float
    target_ml: float
    glasses: float


class WaterHistoryResponse(BaseModel):
    days: List[WaterHistoryDay]
