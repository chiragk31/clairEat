"""
ClairEat Backend — Application Configuration
Loads and validates all environment variables using pydantic-settings.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralised, validated application settings loaded from .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ───────────────────────────────────────────────────────────────
    app_name: str = "ClairEat"
    app_version: str = "1.0.0"
    debug: bool = False
    secret_key: str = "change-me-in-production"
    allowed_origins: List[str] = ["http://localhost:3000"]

    # ── Supabase ──────────────────────────────────────────────────────────
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str

    # ── AI Providers ──────────────────────────────────────────────────────
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"

    # ── Food APIs ─────────────────────────────────────────────────────────
    usda_api_key: str = ""
    nutritionix_app_id: str = ""
    nutritionix_app_key: str = ""
    edamam_app_id: str = ""
    edamam_app_key: str = ""
    spoonacular_api_key: str = ""

    # ── Open APIs (no key required) ───────────────────────────────────────
    open_food_facts_base: str = "https://world.openfoodfacts.org"
    themealdb_base: str = "https://www.themealdb.com/api/json/v1/1"
    open_meteo_base: str = "https://api.open-meteo.com/v1"
    wger_base: str = "https://wger.de/api/v2"

    # ── Rate Limiting ─────────────────────────────────────────────────────
    ai_chat_rate_limit: int = 20          # requests per user per hour
    meal_plan_rate_limit: int = 5         # requests per user per day
    food_search_rate_limit: int = 60      # requests per user per minute

    # ── Caching ───────────────────────────────────────────────────────────
    food_cache_max_size: int = 5000
    food_cache_ttl: int = 86400       # 24 hours
    ai_cache_max_size: int = 1000
    ai_cache_ttl: int = 3600          # 1 hour
    external_cache_max_size: int = 500
    external_cache_ttl: int = 21600   # 6 hours

    # ── Circuit Breaker ───────────────────────────────────────────────────
    ai_failure_threshold: int = 3
    ai_failure_window_seconds: int = 60
    ai_circuit_open_minutes: int = 2

    # ── File Upload ───────────────────────────────────────────────────────
    max_upload_size_mb: int = 5
    allowed_image_types: List[str] = ["image/jpeg", "image/png", "image/webp"]


@lru_cache
def get_settings() -> Settings:
    """Return a cached singleton Settings instance."""
    return Settings()
