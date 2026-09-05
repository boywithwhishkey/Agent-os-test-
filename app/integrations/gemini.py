from __future__ import annotations

import time
from typing import Any

import httpx

from app.core.config import settings
from app.integrations.base import IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult


class GeminiAdapter(IntegrationAdapter):
    """Verifies a Gemini API key by listing available models — a free,
    read-only call — rather than generating content."""

    def __init__(self, *, api_key: str | None = None, client: httpx.AsyncClient | None = None) -> None:
        self.api_key = api_key or settings.gemini_api_key
        self._client = client
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is required")

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            IntegrationProvider.GEMINI,
            request,
            reason="Gemini is used as THYNACT's LLM provider, not a triggered workflow.",
        )

    async def run_capability(self, capability_id: str, arguments: dict[str, Any]) -> object:
        if capability_id == "ai.model.list":
            return {"models": await self._list_models()}
        if capability_id == "ai.completion.create":
            return await self._create_completion(arguments)
        return await super().run_capability(capability_id, arguments)

    async def _list_models(self) -> list[str]:
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await client.get(
                "https://generativelanguage.googleapis.com/v1beta/models",
                headers={"x-goog-api-key": self.api_key},
                params={"pageSize": 100},
                timeout=10.0,
            )
            body = self._json_body(response)
            if response.status_code >= 400:
                raise RuntimeError(f"Gemini returned HTTP {response.status_code}")
            models = body.get("models")
            if not isinstance(models, list):
                raise TypeError("Gemini returned no model list")
            return sorted(
                name.removeprefix("models/")
                for entry in models
                if isinstance(entry, dict)
                and isinstance(name := entry.get("name"), str)
                and name.strip()
            )
        except httpx.TimeoutException as exc:
            raise RuntimeError("Gemini model listing timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Gemini model listing failed: {type(exc).__name__}") from exc
        finally:
            if own_client:
                await client.aclose()

    async def _create_completion(self, arguments: dict[str, Any]) -> dict[str, Any]:
        payload, model = self._completion_payload(arguments)
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                headers={"x-goog-api-key": self.api_key},
                json=payload,
                timeout=30.0,
            )
            body = self._json_body(response)
            if response.status_code >= 400:
                raise RuntimeError(f"Gemini returned HTTP {response.status_code}")
            candidates = body.get("candidates")
            if not isinstance(candidates, list) or not candidates or not isinstance(candidates[0], dict):
                raise RuntimeError("Gemini returned no completion candidates")
            content = candidates[0].get("content")
            parts = content.get("parts") if isinstance(content, dict) else None
            text = "".join(
                part.get("text", "")
                for part in parts or []
                if isinstance(part, dict) and isinstance(part.get("text"), str)
            )
            if not text:
                raise RuntimeError("Gemini returned no text completion")
            return {
                "provider": IntegrationProvider.GEMINI.value,
                "model": model,
                "text": text,
                "finish_reason": candidates[0].get("finishReason"),
                "usage": body.get("usageMetadata"),
            }
        except httpx.TimeoutException as exc:
            raise RuntimeError("Gemini completion timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Gemini completion failed: {type(exc).__name__}") from exc
        finally:
            if own_client:
                await client.aclose()

    @staticmethod
    def _completion_payload(arguments: dict[str, Any]) -> tuple[dict[str, Any], str]:
        model = arguments.get("model")
        if not isinstance(model, str) or not 1 <= len(model.strip()) <= 100:
            raise ValueError("ai.completion.create requires a model")
        model = model.strip().removeprefix("models/")
        if not all(char.isalnum() or char in "._:-" for char in model):
            raise ValueError("model contains unsupported characters")
        messages = arguments.get("messages")
        if not isinstance(messages, list) or not 1 <= len(messages) <= 50:
            raise ValueError("ai.completion.create requires 1-50 messages")
        contents: list[dict[str, Any]] = []
        system_parts: list[str] = []
        total_bytes = 0
        for message in messages:
            if not isinstance(message, dict):
                raise TypeError("each message must be an object")
            role = message.get("role")
            content = message.get("content")
            if role not in {"system", "user", "assistant"}:
                raise ValueError("message role must be system, user, or assistant")
            if not isinstance(content, str) or not 1 <= len(content.strip()) <= 20_000:
                raise ValueError("message content must be 1-20000 characters")
            total_bytes += len(content.encode("utf-8"))
            if role == "system":
                system_parts.append(content)
            else:
                contents.append({"role": "model" if role == "assistant" else "user", "parts": [{"text": content}]})
        if not contents:
            raise ValueError("at least one user or assistant message is required")
        if total_bytes > 100_000:
            raise ValueError("message content must be 100000 UTF-8 bytes or fewer")
        payload: dict[str, Any] = {"contents": contents}
        if system_parts:
            payload["systemInstruction"] = {"parts": [{"text": "\n\n".join(system_parts)}]}
        max_tokens = arguments.get("max_tokens", 1024)
        if isinstance(max_tokens, bool) or not isinstance(max_tokens, int) or not 1 <= max_tokens <= 8192:
            raise ValueError("max_tokens must be an integer between 1 and 8192")
        generation_config: dict[str, Any] = {"maxOutputTokens": max_tokens}
        temperature = arguments.get("temperature")
        if temperature is not None:
            if isinstance(temperature, bool) or not isinstance(temperature, (int, float)) or not 0 <= temperature <= 2:
                raise ValueError("temperature must be between 0 and 2")
            generation_config["temperature"] = temperature
        payload["generationConfig"] = generation_config
        return payload, model

    @staticmethod
    def _json_body(response: httpx.Response) -> dict[str, Any]:
        try:
            body = response.json()
        except ValueError as exc:
            raise RuntimeError("Gemini returned a non-JSON response") from exc
        if not isinstance(body, dict):
            raise TypeError("Gemini returned an invalid response")
        return body

    async def test_connection(self) -> tuple[bool, float | None, str | None]:
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        started = time.perf_counter()
        try:
            response = await client.get(
                "https://generativelanguage.googleapis.com/v1beta/models",
                params={"key": self.api_key, "pageSize": 1},
                timeout=10.0,
            )
            latency_ms = (time.perf_counter() - started) * 1000
            if response.status_code == 200:
                return True, latency_ms, None
            if response.status_code in (400, 401, 403):
                return False, latency_ms, f"Gemini rejected the API key (HTTP {response.status_code})"
            return False, latency_ms, f"Gemini returned HTTP {response.status_code}"
        except httpx.TimeoutException:
            return False, None, "Connection to Gemini timed out"
        except httpx.HTTPError as exc:
            return False, None, f"{type(exc).__name__}: {exc}"
        finally:
            if own_client:
                await client.aclose()
