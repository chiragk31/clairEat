"""
ClairEat — Groq AI Service (Fallback)
Uses Groq's OpenAI-compatible API with LLaMA 3.1 as circuit-breaker fallback.
"""

import asyncio
from typing import Any, AsyncGenerator, Dict, List

import httpx

from app.config import get_settings
from app.core.exceptions import GroqServiceError
from app.core.logging import get_logger
from app.services.ai.prompt_builder import PromptBuilder

logger = get_logger(__name__)

GROQ_BASE_URL = "https://api.groq.com/openai/v1"


class GroqService:
    """OpenAI-compatible wrapper for Groq LLaMA inference."""

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.groq_api_key:
            logger.warning("GROQ_API_KEY not set — Groq fallback disabled")
            self._enabled = False
            return
        self._api_key = settings.groq_api_key
        self._model = settings.groq_model
        self._enabled = True
        logger.info("GroqService initialised", model=self._model)

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    def _build_payload(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        stream: bool = False,
    ) -> Dict[str, Any]:
        groq_messages = [{"role": "system", "content": system_prompt}]
        for msg in messages[-20:]:  # Cap history at 20 messages
            role = msg.get("role", "user")
            # Normalise "assistant" role (Groq uses "assistant")
            groq_messages.append({"role": role, "content": msg.get("content", "")})
        return {
            "model": self._model,
            "messages": groq_messages,
            "stream": stream,
            "max_tokens": 2048,
            "temperature": 0.7,
        }

    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = PromptBuilder.SYSTEM_PROMPT,
    ) -> str:
        """Non-streaming chat completion via Groq.

        Raises:
            GroqServiceError: On any HTTP or decoding error.
        """
        if not self._enabled:
            raise GroqServiceError("Groq API key not configured.")
        payload = self._build_payload(messages, system_prompt, stream=False)
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{GROQ_BASE_URL}/chat/completions",
                    json=payload,
                    headers=self._headers(),
                )
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as exc:
            logger.error("Groq HTTP error", status=exc.response.status_code)
            raise GroqServiceError(f"Groq HTTP {exc.response.status_code}") from exc
        except Exception as exc:
            logger.error("Groq chat error", error=str(exc))
            raise GroqServiceError(f"Groq error: {exc}") from exc

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = PromptBuilder.SYSTEM_PROMPT,
    ) -> AsyncGenerator[str, None]:
        """Streaming chat via Groq — yields text chunks.

        Raises:
            GroqServiceError: On connection or parsing errors.
        """
        if not self._enabled:
            raise GroqServiceError("Groq API key not configured.")
        payload = self._build_payload(messages, system_prompt, stream=True)
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                async with client.stream(
                    "POST",
                    f"{GROQ_BASE_URL}/chat/completions",
                    json=payload,
                    headers=self._headers(),
                ) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if line.startswith("data: "):
                            payload_str = line[6:]
                            if payload_str.strip() == "[DONE]":
                                break
                            import json
                            try:
                                chunk = json.loads(payload_str)
                                delta = chunk["choices"][0]["delta"].get("content", "")
                                if delta:
                                    yield delta
                            except Exception:
                                continue
        except Exception as exc:
            raise GroqServiceError(f"Groq streaming error: {exc}") from exc

    async def generate_json(
        self,
        prompt: str,
        system_prompt: str = PromptBuilder.SYSTEM_PROMPT,
    ) -> str:
        """Single-turn text generation (used as fallback for structured responses)."""
        messages = [{"role": "user", "content": prompt}]
        return await self.chat(messages, system_prompt)
