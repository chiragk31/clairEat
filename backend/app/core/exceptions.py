"""
ClairEat Backend — Custom Exception Classes & Handlers
Centralised application-level exceptions and FastAPI exception handlers.
"""

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


# ── Custom Exception Hierarchy ────────────────────────────────────────────────


class ClairEatError(Exception):
    """Base exception for all ClairEat application errors."""

    def __init__(self, message: str, detail: Any = None) -> None:
        self.message = message
        self.detail = detail
        super().__init__(message)


class NotFoundError(ClairEatError):
    """Resource not found."""


class UnauthorizedError(ClairEatError):
    """Authentication required or token invalid."""


class ForbiddenError(ClairEatError):
    """Authenticated but lacking permission."""


class ValidationError(ClairEatError):
    """Business-rule validation failure (distinct from Pydantic schema errors)."""


class ExternalAPIError(ClairEatError):
    """Failure communicating with an external API."""

    def __init__(self, message: str, api_name: str, detail: Any = None) -> None:
        super().__init__(message, detail)
        self.api_name = api_name


class AIServiceError(ClairEatError):
    """AI provider (Gemini / Groq) error."""


class GeminiRateLimitError(AIServiceError):
    """Gemini rate-limit hit — should trigger fallback."""


class GeminiServiceError(AIServiceError):
    """Gemini service unavailable."""


class GroqServiceError(AIServiceError):
    """Groq service unavailable."""


class RateLimitError(ClairEatError):
    """Per-user rate limit exceeded."""

    def __init__(self, message: str, retry_after: int = 60) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class StorageError(ClairEatError):
    """Supabase Storage operation failure."""


class DuplicateError(ClairEatError):
    """Attempt to create a duplicate resource."""


# ── FastAPI Exception Handlers ────────────────────────────────────────────────


def _error_body(code: str, message: str, detail: Any = None) -> dict:
    payload: dict = {"error": {"code": code, "message": message}}
    if detail is not None:
        payload["error"]["detail"] = detail
    return payload


def register_exception_handlers(app: FastAPI) -> None:
    """Register all custom exception handlers on the FastAPI application."""

    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=_error_body("NOT_FOUND", exc.message, exc.detail),
        )

    @app.exception_handler(UnauthorizedError)
    async def unauthorized_handler(
        request: Request, exc: UnauthorizedError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=_error_body("UNAUTHORIZED", exc.message),
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(ForbiddenError)
    async def forbidden_handler(request: Request, exc: ForbiddenError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=_error_body("FORBIDDEN", exc.message),
        )

    @app.exception_handler(ValidationError)
    async def validation_error_handler(
        request: Request, exc: ValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_error_body("VALIDATION_ERROR", exc.message, exc.detail),
        )

    @app.exception_handler(RateLimitError)
    async def rate_limit_handler(
        request: Request, exc: RateLimitError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content=_error_body("RATE_LIMIT_EXCEEDED", exc.message),
            headers={"Retry-After": str(exc.retry_after)},
        )

    @app.exception_handler(ExternalAPIError)
    async def external_api_handler(
        request: Request, exc: ExternalAPIError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content=_error_body(
                "EXTERNAL_API_ERROR",
                f"{exc.api_name}: {exc.message}",
                exc.detail,
            ),
        )

    @app.exception_handler(AIServiceError)
    async def ai_service_handler(
        request: Request, exc: AIServiceError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=_error_body("AI_SERVICE_ERROR", exc.message),
        )

    @app.exception_handler(DuplicateError)
    async def duplicate_handler(request: Request, exc: DuplicateError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=_error_body("DUPLICATE", exc.message),
        )

    @app.exception_handler(StorageError)
    async def storage_handler(request: Request, exc: StorageError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_body("STORAGE_ERROR", exc.message),
        )

    @app.exception_handler(Exception)
    async def generic_handler(request: Request, exc: Exception) -> JSONResponse:
        """Catch-all for unhandled exceptions — never expose internals."""
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_body("INTERNAL_ERROR", "An unexpected error occurred."),
        )
