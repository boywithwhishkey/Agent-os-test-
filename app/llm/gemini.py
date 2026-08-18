from __future__ import annotations

import asyncio
import os

from .base import LLMProvider, LLMRequest


class GeminiLLMProvider(LLMProvider):
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model or os.getenv(
            "AGENT_OS_LLM_MODEL", "gemini-3.1-flash-lite"
        )
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is required for the Gemini provider.")

    async def generate(self, request: LLMRequest) -> str:
        try:
            from google import genai
        except ImportError as exc:
            raise RuntimeError(
                "Gemini provider requires the 'google-genai' package."
            ) from exc

        def _call() -> str:
            client = genai.Client(api_key=self.api_key)
            prompt = f"{request.system}\n\nUSER TASK:\n{request.prompt}"
            response = client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
            text = getattr(response, "text", None)
            if not text or not text.strip():
                raise RuntimeError("Gemini returned an empty response.")
            return text.strip()

        return await asyncio.to_thread(_call)
