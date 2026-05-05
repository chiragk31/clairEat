"""
ClairEat Backend — FastAPI Application Entry Point
Configures CORS, lifespan, routers, exception handlers, and health check.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.core.supabase_client import close_supabase, get_supabase

# ── Routers ───────────────────────────────────────────────────────────────────
from app.routers import (
    ai_coach,
    analytics,
    auth,
    food,
    habits,
    insights,
    meal_plans,
    meals,
    profile,
    water,
)

settings = get_settings()
configure_logging(debug=settings.debug)
logger = get_logger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifecycle management."""
    logger.info(
        "ClairEat backend starting",
        version=settings.app_version,
        debug=settings.debug,
    )
    # Warm up Supabase connection
    await get_supabase()
    logger.info("Supabase connection initialised")

    yield  # Application runs here

    logger.info("ClairEat backend shutting down")
    await close_supabase()


# ── Application Factory ───────────────────────────────────────────────────────

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="ClairEat API",
        description=(
            "Intelligent nutrition and habit platform. "
            "AI-powered meal scoring, food search, habit tracking, and personalised coaching."
        ),
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ── Middleware ────────────────────────────────────────────────────────

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if not settings.debug:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["api.claireat.com", "*.claireat.com", "localhost"],
        )

    # ── Exception Handlers ────────────────────────────────────────────────

    register_exception_handlers(app)

    # ── Routers ───────────────────────────────────────────────────────────

    API_PREFIX = "/v1"
    app.include_router(auth.router, prefix=API_PREFIX)
    app.include_router(profile.router, prefix=API_PREFIX)
    app.include_router(food.router, prefix=API_PREFIX)
    app.include_router(meals.router, prefix=API_PREFIX)
    app.include_router(meal_plans.router, prefix=API_PREFIX)
    app.include_router(habits.router, prefix=API_PREFIX)
    app.include_router(water.router, prefix=API_PREFIX)
    app.include_router(ai_coach.router, prefix=API_PREFIX)
    app.include_router(insights.router, prefix=API_PREFIX)
    app.include_router(analytics.router, prefix=API_PREFIX)

    # ── Health & Meta ──────────────────────────────────────────────────────

    @app.get("/", tags=["Health"], summary="Root — redirect info")
    async def root() -> dict:
        return {
            "app": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
            "health": "/health",
        }

    @app.get("/health", tags=["Health"], summary="Health check")
    async def health() -> dict:
        from app.core.cache import cache_manager
        return {
            "status": "healthy",
            "version": settings.app_version,
            "cache": cache_manager.stats(),
        }

    return app


app = create_app()
