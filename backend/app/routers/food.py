"""
ClairEat — Food Router
Unified food search, barcode lookup, NLP parsing, custom foods, and user history.
"""

from fastapi import APIRouter, Query

from app.config import get_settings
from app.core.rate_limiter import check_rate_limit
from app.dependencies import DBDep, UserDep
from app.schemas.food import (
    CustomFoodRequest,
    FoodItemResponse,
    FoodSearchResponse,
    NLPParseResponse,
)
from app.services.food.food_service import FoodSearchService

router = APIRouter(prefix="/food", tags=["Food Database"])


@router.get(
    "/search",
    response_model=FoodSearchResponse,
    summary="Search food across all sources",
    description="Cascade: L1 cache → Supabase → Open Food Facts + USDA (parallel) → Nutritionix.",
)
async def search_food(
    q: str = Query(min_length=2, max_length=200, description="Food name or keyword"),
    limit: int = Query(default=10, ge=1, le=30),
    user: UserDep = None,
    db: DBDep = None,
) -> FoodSearchResponse:
    settings = get_settings()
    await check_rate_limit(user.id, "food_search", settings.food_search_rate_limit, 60)
    svc = FoodSearchService(db)
    results = await svc.search(q, limit)
    return FoodSearchResponse(
        results=[_to_item_response(r) for r in results],
        total=len(results),
    )


@router.get(
    "/barcode/{barcode}",
    response_model=FoodItemResponse,
    summary="Look up food by EAN/UPC barcode",
)
async def lookup_barcode(barcode: str, user: UserDep, db: DBDep) -> FoodItemResponse:
    from app.core.exceptions import NotFoundError
    svc = FoodSearchService(db)
    item = await svc.lookup_barcode(barcode)
    if not item:
        raise NotFoundError(f"No food found for barcode: {barcode}")
    return _to_item_response(item)


@router.get(
    "/nlp",
    response_model=NLPParseResponse,
    summary="Parse natural language food description",
    description="E.g. '2 boiled eggs and a banana' → structured food items with nutrition.",
)
async def nlp_parse(
    q: str = Query(min_length=3, max_length=500),
    user: UserDep = None,
    db: DBDep = None,
) -> NLPParseResponse:
    svc = FoodSearchService(db)
    items = await svc.natural_language_parse(q)
    return NLPParseResponse(parsed_items=items, raw_query=q)


@router.get(
    "/favorites",
    response_model=FoodSearchResponse,
    summary="Get user's most-logged favourite foods",
)
async def get_favorites(user: UserDep, db: DBDep) -> FoodSearchResponse:
    svc = FoodSearchService(db)
    results = await svc.get_user_favorites(user.id)
    return FoodSearchResponse(results=[_to_item_response(r) for r in results], total=len(results))


@router.get(
    "/history",
    response_model=FoodSearchResponse,
    summary="Get recently logged foods",
)
async def get_history(user: UserDep, db: DBDep) -> FoodSearchResponse:
    svc = FoodSearchService(db)
    results = await svc.get_user_food_history(user.id)
    return FoodSearchResponse(results=[_to_item_response(r) for r in results], total=len(results))


@router.get(
    "/{food_id}",
    response_model=FoodItemResponse,
    summary="Get full food item details",
)
async def get_food_detail(food_id: str, user: UserDep, db: DBDep) -> FoodItemResponse:
    from app.core.exceptions import NotFoundError
    svc = FoodSearchService(db)
    item = await svc.get_by_id(food_id)
    if not item:
        raise NotFoundError(f"Food item {food_id} not found.")
    return _to_item_response(item)


@router.post(
    "/custom",
    response_model=FoodItemResponse,
    status_code=201,
    summary="Save a custom food item",
)
async def create_custom_food(
    request: CustomFoodRequest, user: UserDep, db: DBDep
) -> FoodItemResponse:
    svc = FoodSearchService(db)
    item = await svc.save_custom_food(user.id, request.model_dump())
    return _to_item_response(item)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _to_item_response(data: dict) -> FoodItemResponse:
    return FoodItemResponse(
        id=data.get("id") or "",
        external_id=data.get("external_id"),
        source=data.get("source"),
        name=data.get("name") or "Unknown",
        brand=data.get("brand"),
        barcode=data.get("barcode"),
        serving_size_g=data.get("serving_size_g"),
        serving_unit=data.get("serving_unit"),
        calories_per_100g=data.get("calories_per_100g"),
        protein_per_100g=data.get("protein_per_100g"),
        carbs_per_100g=data.get("carbs_per_100g"),
        fat_per_100g=data.get("fat_per_100g"),
        fiber_per_100g=data.get("fiber_per_100g"),
        sugar_per_100g=data.get("sugar_per_100g"),
        sodium_per_100g=data.get("sodium_per_100g"),
        vitamins=data.get("vitamins") or {},
        minerals=data.get("minerals") or {},
        nutriscore=data.get("nutriscore"),
        nova_group=data.get("nova_group"),
        allergens=data.get("allergens") or [],
        image_url=data.get("image_url"),
    )
