"""
ClairEat — Auth Router
Handles registration, login, logout, token refresh, and Google OAuth.
"""

from fastapi import APIRouter, Depends
from supabase import AsyncClient

from app.core.exceptions import UnauthorizedError, DuplicateError
from app.core.logging import get_logger
from app.dependencies import DBDep, UserDep
from app.schemas.auth import (
    GoogleAuthResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=201,
    summary="Register a new user",
    description="Create a new account with email and password. Returns JWT tokens.",
)
async def register(request: RegisterRequest, db: DBDep) -> TokenResponse:
    """Register a new user via Supabase Auth."""
    try:
        resp = await db.auth.sign_up({
            "email": request.email,
            "password": request.password,
            "options": {
                "data": {"full_name": request.full_name or ""}
            },
        })
        if resp.user is None:
            raise DuplicateError("An account with this email already exists.")

        session = resp.session
        logger.info("User registered", user_id=str(resp.user.id))
        return TokenResponse(
            access_token=session.access_token,
            refresh_token=session.refresh_token,
            expires_in=session.expires_in or 3600,
        )
    except DuplicateError:
        raise
    except Exception as exc:
        if "already registered" in str(exc).lower() or "already exists" in str(exc).lower():
            raise DuplicateError("An account with this email already exists.")
        logger.error("Registration failed", error=str(exc))
        raise UnauthorizedError("Registration failed. Please try again.")


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in with email and password",
)
async def login(request: LoginRequest, db: DBDep) -> TokenResponse:
    """Authenticate user and return JWT access + refresh tokens."""
    try:
        resp = await db.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password,
        })
        session = resp.session
        if session is None:
            raise UnauthorizedError("Invalid email or password.")
        logger.info("User logged in", user_id=str(resp.user.id))
        return TokenResponse(
            access_token=session.access_token,
            refresh_token=session.refresh_token,
            expires_in=session.expires_in or 3600,
        )
    except UnauthorizedError:
        raise
    except Exception as exc:
        logger.warning("Login failed", error=str(exc))
        raise UnauthorizedError("Invalid email or password.")


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh an expired access token",
)
async def refresh_token(request: RefreshRequest, db: DBDep) -> TokenResponse:
    """Exchange a valid refresh token for a new access token."""
    try:
        resp = await db.auth.refresh_session(request.refresh_token)
        session = resp.session
        if session is None:
            raise UnauthorizedError("Refresh token is invalid or expired.")
        return TokenResponse(
            access_token=session.access_token,
            refresh_token=session.refresh_token,
            expires_in=session.expires_in or 3600,
        )
    except UnauthorizedError:
        raise
    except Exception as exc:
        raise UnauthorizedError("Could not refresh token.")


@router.post(
    "/logout",
    status_code=204,
    summary="Log out current session",
)
async def logout(user: UserDep, db: DBDep) -> None:
    """Invalidate the current Supabase session."""
    try:
        await db.auth.sign_out()
        logger.info("User logged out", user_id=user.id)
    except Exception:
        pass  # Best-effort logout


@router.post(
    "/google",
    response_model=GoogleAuthResponse,
    summary="Initiate Google OAuth via Supabase",
)
async def google_oauth(db: DBDep) -> GoogleAuthResponse:
    """Return the Google OAuth redirect URL from Supabase Auth."""
    try:
        resp = await db.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {"redirect_to": "https://claireat.com/auth/callback"},
        })
        return GoogleAuthResponse(redirect_url=str(resp.url) if resp.url else None)
    except Exception as exc:
        logger.error("Google OAuth initiation failed", error=str(exc))
        return GoogleAuthResponse(message="Google OAuth not configured.")
