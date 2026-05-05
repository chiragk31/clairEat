"""
ClairEat — Google Gemini AI Service
Handles chat (streaming & non-streaming) and structured JSON generation.
"""

import asyncio
from typing import Any, AsyncGenerator, Dict, List, Optional

import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable

from app.config import get_settings
from app.core.exceptions import GeminiRateLimitError, GeminiServiceError
from app.core.logging import get_logger
from app.services.ai.prompt_builder import PromptBuilder

logger = get_logger(__name__)


class GeminiService:
    """Wrapper around Google Gemini Flash for chat and JSON-mode inference."""

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.gemini_api_key:
            logger.warning("GEMINI_API_KEY not set — Gemini service disabled")
            self._enabled = False
            return
        genai.configure(api_key=settings.gemini_api_key)
        self._model_name = settings.gemini_model
        self._enabled = True
        logger.info("GeminiService initialised", model=self._model_name)

    def _get_model(self, system_prompt: Optional[str] = None) -> genai.GenerativeModel:
        kwargs: Dict[str, Any] = {"model_name": self._model_name}
        if system_prompt:
            kwargs["system_instruction"] = system_prompt
        return genai.GenerativeModel(**kwargs)

    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = PromptBuilder.SYSTEM_PROMPT,
    ) -> str:
        """Non-streaming chat completion.

        Args:
            messages:      List of {"role": "user"|"model", "content": str}.
            system_prompt: System instruction injected at model level.

        Returns:
            Full response text.

        Raises:
            GeminiRateLimitError: On 429 from Google API.
            GeminiServiceError:   On any other Gemini error.
        """
        if not self._enabled:
            raise GeminiServiceError("Gemini API key not configured.")
        try:
            model = self._get_model(system_prompt)
            # Convert to Gemini-style history
            history = self._to_gemini_history(messages[:-1])
            chat_session = model.start_chat(history=history)
            last_message = messages[-1]["content"] if messages else ""
            response = await asyncio.to_thread(chat_session.send_message, last_message)
            return response.text
        except ResourceExhausted as exc:
            logger.warning("Gemini rate limit hit", error=str(exc))
            raise GeminiRateLimitError("Gemini rate limit exceeded.") from exc
        except (ServiceUnavailable, Exception) as exc:
            logger.error("Gemini chat error", error=str(exc))
            raise GeminiServiceError(f"Gemini error: {exc}") from exc

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = PromptBuilder.SYSTEM_PROMPT,
    ) -> AsyncGenerator[str, None]:
        """Streaming chat — yields text chunks as they arrive.

        Raises:
            GeminiRateLimitError / GeminiServiceError on failure.
        """
        if not self._enabled:
            raise GeminiServiceError("Gemini API key not configured.")
        try:
            model = self._get_model(system_prompt)
            history = self._to_gemini_history(messages[:-1])
            chat_session = model.start_chat(history=history)
            last_message = messages[-1]["content"] if messages else ""

            # Gemini streaming is synchronous; run in thread
            def _stream():
                return chat_session.send_message(last_message, stream=True)

            response = await asyncio.to_thread(_stream)
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except ResourceExhausted as exc:
            raise GeminiRateLimitError("Gemini rate limit exceeded.") from exc
        except Exception as exc:
            raise GeminiServiceError(f"Gemini streaming error: {exc}") from exc

    async def generate_json(
        self,
        prompt: str,
        system_prompt: str = PromptBuilder.SYSTEM_PROMPT,
    ) -> str:
        """Single-turn JSON-focused generation (used for meal plans, scores)."""
        if not self._enabled:
            raise GeminiServiceError("Gemini API key not configured.")
        try:
            model = self._get_model(system_prompt)
            response = await asyncio.to_thread(model.generate_content, prompt)
            return response.text
        except ResourceExhausted as exc:
            raise GeminiRateLimitError("Gemini rate limit exceeded.") from exc
        except Exception as exc:
            raise GeminiServiceError(f"Gemini generate_json error: {exc}") from exc

    @staticmethod
    def _to_gemini_history(
        messages: List[Dict[str, str]],
    ) -> List[Dict[str, Any]]:
        """Convert generic message list to Gemini history format."""
        result = []
        for msg in messages[-20:]:  # Cap at 20 messages to manage context window
            role = "model" if msg.get("role") == "assistant" else "user"
            result.append({"role": role, "parts": [msg.get("content", "")]})
        return result
