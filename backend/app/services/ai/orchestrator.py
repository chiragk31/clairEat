"""
ClairEat — AI Orchestrator with Circuit Breaker
Routes requests to Gemini (primary) with automatic Groq fallback.
Circuit breaker pattern prevents hammering a failing primary provider.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, AsyncGenerator, Dict, List, Optional

from app.config import get_settings
from app.core.exceptions import (
    AIServiceError,
    GeminiRateLimitError,
    GeminiServiceError,
    GroqServiceError,
)
from app.core.logging import get_logger
from app.services.ai.gemini_service import GeminiService
from app.services.ai.groq_service import GroqService
from app.services.ai.prompt_builder import PromptBuilder

logger = get_logger(__name__)


class AIOrchestrator:
    """Routes AI requests to Gemini first, falls back to Groq on failure.

    Circuit Breaker States:
        CLOSED  → Normal: requests go to Gemini.
        OPEN    → Gemini failed ≥N times in window; route all to Groq for T minutes.
        HALF    → After T minutes, test Gemini again.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._gemini = GeminiService()
        self._groq = GroqService()
        self._failure_threshold = settings.ai_failure_threshold
        self._failure_window_s = settings.ai_failure_window_seconds
        self._circuit_open_duration = timedelta(minutes=settings.ai_circuit_open_minutes)
        self._primary_failures = 0
        self._circuit_open_until: Optional[datetime] = None
        self._lock = asyncio.Lock()

    # ── Public Interface ──────────────────────────────────────────────────

    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = PromptBuilder.SYSTEM_PROMPT,
    ) -> str:
        """Non-streaming chat. Returns full response string."""
        if await self._is_circuit_open():
            return await self._groq_chat(messages, system_prompt)
        try:
            result = await self._gemini.chat(messages, system_prompt)
            await self._reset_failures()
            return result
        except (GeminiRateLimitError, GeminiServiceError) as exc:
            await self._record_failure()
            logger.warning("Gemini failed, falling back to Groq", error=str(exc))
            return await self._groq_chat(messages, system_prompt)

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = PromptBuilder.SYSTEM_PROMPT,
    ) -> AsyncGenerator[str, None]:
        """Streaming chat — yields text chunks. Falls back to Groq if Gemini fails."""
        if await self._is_circuit_open():
            async for chunk in self._groq.stream_chat(messages, system_prompt):
                yield chunk
            return
        try:
            async for chunk in self._gemini.stream_chat(messages, system_prompt):
                yield chunk
            await self._reset_failures()
        except (GeminiRateLimitError, GeminiServiceError) as exc:
            await self._record_failure()
            logger.warning("Gemini stream failed, falling back to Groq", error=str(exc))
            async for chunk in self._groq.stream_chat(messages, system_prompt):
                yield chunk

    async def generate_json(self, prompt: str) -> str:
        """Single-turn JSON generation. Falls back to Groq on Gemini failure."""
        if await self._is_circuit_open():
            return await self._groq.generate_json(prompt)
        try:
            result = await self._gemini.generate_json(prompt)
            await self._reset_failures()
            return result
        except (GeminiRateLimitError, GeminiServiceError) as exc:
            await self._record_failure()
            logger.warning("Gemini JSON generation failed, falling back", error=str(exc))
            return await self._groq.generate_json(prompt)

    def current_provider(self) -> str:
        """Which provider is currently being used (for observability)."""
        if self._circuit_open_until and datetime.now() < self._circuit_open_until:
            return "groq"
        return "gemini"

    # ── Circuit Breaker Logic ─────────────────────────────────────────────

    async def _is_circuit_open(self) -> bool:
        async with self._lock:
            if self._circuit_open_until and datetime.now() < self._circuit_open_until:
                return True
            if self._circuit_open_until and datetime.now() >= self._circuit_open_until:
                # Half-open: allow one test through Gemini
                self._circuit_open_until = None
                self._primary_failures = 0
            return False

    async def _record_failure(self) -> None:
        async with self._lock:
            self._primary_failures += 1
            logger.debug(
                "Gemini failure recorded",
                count=self._primary_failures,
                threshold=self._failure_threshold,
            )
            if self._primary_failures >= self._failure_threshold:
                self._circuit_open_until = datetime.now() + self._circuit_open_duration
                logger.warning(
                    "Circuit breaker OPEN — routing to Groq",
                    open_until=str(self._circuit_open_until),
                )

    async def _reset_failures(self) -> None:
        async with self._lock:
            self._primary_failures = 0
            self._circuit_open_until = None

    async def _groq_chat(
        self, messages: List[Dict[str, str]], system_prompt: str
    ) -> str:
        try:
            return await self._groq.chat(messages, system_prompt)
        except GroqServiceError as exc:
            logger.error("Both Gemini and Groq failed", error=str(exc))
            raise AIServiceError("All AI providers are currently unavailable.") from exc


# Application-scoped singleton
_orchestrator: Optional[AIOrchestrator] = None


def get_ai_orchestrator() -> AIOrchestrator:
    """Return the global AI orchestrator singleton."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AIOrchestrator()
    return _orchestrator
