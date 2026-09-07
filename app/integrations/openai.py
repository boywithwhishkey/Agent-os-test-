from __future__ import annotations

import time
from typing import Any

import httpx

from app.core.config import settings
from app.integrations.base import IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult


class OpenAIAdapter(IntegrationAdapter):
    """Verifies an OpenAI API key with a harmless, free read call (listing
    models) rather than an actual chat completion. THYNACT uses OpenAI only
    as an optional alternate LLM provider, not for triggered workflows, so
    execute() is intentionally unsupported here."""

    def __init__(self, *, api_key: str | None = None, client: httpx.AsyncClient | None = None) -> None:
        self.api_key = api_key or settings.connector_credential(
            "OPENAI_API_KEY", settings.openai_api_key
        )
        self._client = client
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is required")

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            IntegrationProvider.OPENAI,
            request,
            reason="OpenAI is a model provider, not a triggered workflow; use it as an LLM provider instead.",
        )

    async def run_capability(self, capability_id: str, arguments: dict) -> object:
        """`ai.model.list` — the model ids this key can actually reach.

        Same free, read-only request `test_connection` already makes; that one
        throws the body away, this one returns it. Nothing else is wired: the
        broker reports an unwired capability honestly rather than this adapter
        inventing a result.
        """
        if capability_id == "ai.model.list":
            return {"models": await self._list_models()}
        if capability_id == "ai.completion.create":
            return await self._create_completion(arguments)
        return await super().run_capability(capability_id, arguments)

    async def _create_completion(self, arguments: dict[str, Any]) -> dict[str, Any]:
        payload = self._completion_payload(arguments)
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
                timeout=30.0,
            )
            body = self._json_body(response, "OpenAI")
            if response.status_code >= 400:
                raise RuntimeError(f"OpenAI returned HTTP {response.status_code}")
            choices = body.get("choices")
            if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
                raise RuntimeError("OpenAI returned no completion choices")
            message = choices[0].get("message")
            text = message.get("content") if isinstance(message, dict) else None
            if not isinstance(text, str):
                raise TypeError("OpenAI returned no text completion")
            return {
                "provider": IntegrationProvider.OPENAI.value,
                "model": payload["model"],
                "text": text,
                "finish_reason": choices[0].get("finish_reason"),
                "usage": body.get("usage"),
            }
        except httpx.TimeoutException as exc:
            raise RuntimeError("OpenAI completion timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"OpenAI completion failed: {type(exc).__name__}") from exc
        finally:
            if own_client:
                await client.aclose()

    @staticmethod
    def _completion_payload(arguments: dict[str, Any]) -> dict[str, Any]:
        model = arguments.get("model")
        if not isinstance(model, str) or not 1 <= len(model.strip()) <= 100:
            raise ValueError("ai.completion.create requires a model")
        messages = _messages(arguments)
        payload: dict[str, Any] = {"model": model.strip(), "messages": messages}
        max_tokens = arguments.get("max_tokens", 1024)
        if isinstance(max_tokens, bool) or not isinstance(max_tokens, int) or not 1 <= max_tokens <= 8192:
            raise ValueError("max_tokens must be an integer between 1 and 8192")
        payload["max_tokens"] = max_tokens
        temperature = arguments.get("temperature")
        if temperature is not None:
            if isinstance(temperature, bool) or not isinstance(temperature, (int, float)) or not 0 <= temperature <= 2:
                raise ValueError("temperature must be between 0 and 2")
            payload["temperature"] = temperature
        return payload

    @staticmethod
    def _json_body(response: httpx.Response, provider: str) -> dict[str, Any]:
        try:
            body = response.json()
        except ValueError as exc:
            raise RuntimeError(f"{provider} returned a non-JSON response") from exc
        if not isinstance(body, dict):
            raise TypeError(f"{provider} returned an invalid response")
        return body

    async def _list_models(self) -> list[str]:
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await client.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10.0,
            )
            response.raise_for_status()
            payload = response.json()
            return sorted(m["id"] for m in payload.get("data", []) if "id" in m)
        finally:
            if own_client:
                await client.aclose()

    async def test_connection(self) -> tuple[bool, float | None, str | None]:
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        started = time.perf_counter()
        try:
            response = await client.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10.0,
            )
            latency_ms = (time.perf_counter() - started) * 1000
            if response.status_code == 200:
                return True, latency_ms, None
            if response.status_code == 401:
                return False, latency_ms, "OpenAI rejected the API key (HTTP 401)"
            return False, latency_ms, f"OpenAI returned HTTP {response.status_code}"
        except httpx.TimeoutException:
            return False, None, "Connection to OpenAI timed out"
        except httpx.HTTPError as exc:
            return False, None, f"{type(exc).__name__}: {exc}"
        finally:
            if own_client:
                await client.aclose()


def _messages(arguments: dict[str, Any]) -> list[dict[str, str]]:
    messages = arguments.get("messages")
    if not isinstance(messages, list) or not 1 <= len(messages) <= 50:
        raise ValueError("ai.completion.create requires 1-50 messages")
    normalized: list[dict[str, str]] = []
    total_bytes = 0
    for message in messages:
        if not isinstance(message, dict):
            raise TypeError("each message must be an object")
        role = message.get("role")
        content = message.get("content")
        if role not in {"system", "developer", "user", "assistant"}:
            raise ValueError("message role must be system, developer, user, or assistant")
        if not isinstance(content, str) or not 1 <= len(content.strip()) <= 20_000:
            raise ValueError("message content must be 1-20000 characters")
        total_bytes += len(content.encode("utf-8"))
        normalized.append({"role": role, "content": content})
    if total_bytes > 100_000:
        raise ValueError("message content must be 100000 UTF-8 bytes or fewer")
    return normalized
