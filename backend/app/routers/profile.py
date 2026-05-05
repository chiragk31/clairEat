"""
ClairEat — Profile Router
CRUD for user profiles, onboarding, and TDEE calculations.
"""

from fastapi import APIRouter

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.dependencies import DBDep, UserDep
from app.schemas.profile import (
    OnboardingRequest,
    OnboardingResponse,
    ProfileResponse,
    ProfileUpdateRequest,
    TDEEResult,
)
from app.utils.tdee_calculator import TDEECalculator
from datetime import datetime

logger = get_logger(__name__)
router = APIRouter(prefix="/profile", tags=["Profile"])


@router.post(
    "/onboarding",
    response_model=OnboardingResponse,
    status_code=201,
    summary="Complete user onboarding",
    description="Save full profile, compute TDEE, and set macro targets. Marks onboarding complete.",
)
async def complete_onboarding(
    request: OnboardingRequest, user: UserDep, db: DBDep
) -> OnboardingResponse:
    """Complete onboarding flow — persists profile and auto-computes TDEE + macros."""
    tdee = TDEECalculator.calculate(
        age=request.age,
        gender=request.gender,
        weight_kg=request.weight_kg,
        height_cm=request.height_cm,
        activity_level=request.activity_level,
        health_goals=request.health_goals,
    )

    profile_data = {
        "id": user.id,
        "full_name": request.full_name,
        "age": request.age,
        "gender": request.gender,
        "height_cm": request.height_cm,
        "weight_kg": request.weight_kg,
        "target_weight_kg": request.target_weight_kg,
        "activity_level": request.activity_level,
        "health_goals": request.health_goals,
        "dietary_restrictions": request.dietary_restrictions,
        "allergies": request.allergies,
        "timezone": request.timezone,
        "location_city": request.location_city,
        "daily_calorie_target": int(tdee.goal_calories),
        "daily_protein_target_g": tdee.protein_g,
        "daily_carb_target_g": tdee.carbs_g,
        "daily_fat_target_g": tdee.fat_g,
        "onboarding_complete": True,
        "updated_at": datetime.utcnow().isoformat(),
    }

    # Upsert profile
    resp = await db.table("profiles").upsert(profile_data, on_conflict="id").execute()
    profile = resp.data[0]

    # Persist TDEE calculation record
    await db.table("tdee_calculations").insert({
        "user_id": user.id,
        "bmr": tdee.bmr,
        "tdee": tdee.tdee,
        "goal_calories": tdee.goal_calories,
        "formula_used": "mifflin_st_jeor",
        "calculated_at": datetime.utcnow().isoformat(),
    }).execute()

    logger.info("Onboarding complete", user_id=user.id)
    return OnboardingResponse(
        profile=_to_profile_response(profile),
        tdee=TDEEResult(**tdee.to_dict()),
    )


@router.get(
    "",
    response_model=ProfileResponse,
    summary="Get current user profile",
)
async def get_profile(user: UserDep, db: DBDep) -> ProfileResponse:
    """Fetch the authenticated user's full profile."""
    resp = (
        await db.table("profiles")
        .select("*")
        .eq("id", user.id)
        .single()
        .execute()
    )
    if not resp.data:
        raise NotFoundError("Profile not found. Please complete onboarding.")
    return _to_profile_response(resp.data)


@router.put(
    "",
    response_model=ProfileResponse,
    summary="Update profile fields (partial update supported)",
)
async def update_profile(
    request: ProfileUpdateRequest, user: UserDep, db: DBDep
) -> ProfileResponse:
    """Partial profile update. Recalculates TDEE if body composition fields change."""
    updates = request.model_dump(exclude_none=True)
    if not updates:
        return await get_profile(user, db)

    updates["updated_at"] = datetime.utcnow().isoformat()

    # Recalculate TDEE if relevant fields changed
    body_fields = {"age", "gender", "weight_kg", "height_cm", "activity_level", "health_goals"}
    if updates.keys() & body_fields:
        current = (
            await db.table("profiles").select("*").eq("id", user.id).single().execute()
        ).data or {}
        merged = {**current, **updates}
        if all(merged.get(f) for f in ["age", "gender", "weight_kg", "height_cm", "activity_level"]):
            tdee = TDEECalculator.calculate(
                age=int(merged["age"]),
                gender=merged["gender"],
                weight_kg=float(merged["weight_kg"]),
                height_cm=float(merged["height_cm"]),
                activity_level=merged["activity_level"],
                health_goals=merged.get("health_goals") or [],
            )
            updates["daily_calorie_target"] = int(tdee.goal_calories)
            updates["daily_protein_target_g"] = tdee.protein_g
            updates["daily_carb_target_g"] = tdee.carbs_g
            updates["daily_fat_target_g"] = tdee.fat_g

    resp = (
        await db.table("profiles")
        .update(updates)
        .eq("id", user.id)
        .execute()
    )
    return _to_profile_response(resp.data[0])


@router.get(
    "/tdee",
    response_model=TDEEResult,
    summary="Get latest TDEE calculation",
)
async def get_tdee(user: UserDep, db: DBDep) -> TDEEResult:
    """Return the most recent TDEE calculation for the user."""
    resp = (
        await db.table("tdee_calculations")
        .select("*")
        .eq("user_id", user.id)
        .order("calculated_at", desc=True)
        .limit(1)
        .execute()
    )
    if not resp.data:
        raise NotFoundError("No TDEE calculation found. Please complete onboarding.")
    row = resp.data[0]
    return TDEEResult(
        bmr=row["bmr"],
        tdee=row["tdee"],
        goal_calories=row["goal_calories"],
        protein_g=0, carbs_g=0, fat_g=0,  # Legacy record, derive from profile
        formula=row.get("formula_used", "mifflin_st_jeor"),
    )


# ── Helpers ───────────────────────────────────────────────────────────────────


def _to_profile_response(data: dict) -> ProfileResponse:
    return ProfileResponse(
        id=data["id"],
        username=data.get("username"),
        full_name=data.get("full_name"),
        age=data.get("age"),
        gender=data.get("gender"),
        height_cm=data.get("height_cm"),
        weight_kg=data.get("weight_kg"),
        target_weight_kg=data.get("target_weight_kg"),
        activity_level=data.get("activity_level"),
        health_goals=data.get("health_goals") or [],
        dietary_restrictions=data.get("dietary_restrictions") or [],
        allergies=data.get("allergies") or [],
        daily_calorie_target=data.get("daily_calorie_target"),
        daily_protein_target_g=data.get("daily_protein_target_g"),
        daily_carb_target_g=data.get("daily_carb_target_g"),
        daily_fat_target_g=data.get("daily_fat_target_g"),
        timezone=data.get("timezone") or "UTC",
        location_city=data.get("location_city"),
        onboarding_complete=data.get("onboarding_complete") or False,
        created_at=str(data.get("created_at", "")),
        updated_at=str(data.get("updated_at", "")),
    )
