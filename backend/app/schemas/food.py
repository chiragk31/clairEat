"""ClairEat — Food Schemas"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FoodItemResponse(BaseModel):
    id: str
    external_id: Optional[str] = None
    source: Optional[str] = None
    name: str
    brand: Optional[str] = None
    barcode: Optional[str] = None
    serving_size_g: Optional[float] = None
    serving_unit: Optional[str] = None
    calories_per_100g: Optional[float] = None
    protein_per_100g: Optional[float] = None
    carbs_per_100g: Optional[float] = None
    fat_per_100g: Optional[float] = None
    fiber_per_100g: Optional[float] = None
    sugar_per_100g: Optional[float] = None
    sodium_per_100g: Optional[float] = None
    vitamins: Dict[str, Any] = {}
    minerals: Dict[str, Any] = {}
    nutriscore: Optional[str] = None
    nova_group: Optional[int] = None
    allergens: List[str] = []
    image_url: Optional[str] = None


class FoodSearchResponse(BaseModel):
    results: List[FoodItemResponse]
    total: int
    source: str = "cache+external"


class NLPFoodItem(BaseModel):
    name: str
    quantity_g: float
    calories: float
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None


class NLPParseResponse(BaseModel):
    parsed_items: List[NLPFoodItem]
    raw_query: str


class CustomFoodRequest(BaseModel):
    name: str = Field(max_length=200)
    brand: Optional[str] = Field(default=None, max_length=200)
    serving_size_g: Optional[float] = Field(default=None, gt=0)
    calories_per_100g: float = Field(gt=0)
    protein_per_100g: Optional[float] = Field(default=None, ge=0)
    carbs_per_100g: Optional[float] = Field(default=None, ge=0)
    fat_per_100g: Optional[float] = Field(default=None, ge=0)
    fiber_per_100g: Optional[float] = Field(default=None, ge=0)
    allergens: List[str] = Field(default_factory=list)
