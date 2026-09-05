from __future__ import annotations

import time
from typing import Any

import httpx

from app.core.config import settings
from app.integrations.base import IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult

ANTHROPIC_API_VERSION = "2023-06-01"


class AnthropicAdapter(IntegrationAdapter):
    """Verifies an Anthropic API key with a harmless, free read call (listing
    models) rather than an actual message. THYNACT does not currently run
    Claude as an LLM provider itself, so execute() is unsupported here."""

    def __init__(self, *, api_key: str | None = None, client: httpx.AsyncClient | None = None) -> None:
        self.api_key = api_key or settings.anthropic_api_key
        self._client = client
        if not self.api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is required")

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            IntegrationProvider.ANTHROPIC,
            request,
            reason="Anthropic is a model provider, not a triggered workflow.",
        )

    async def run_capability(self, capability_id: str, arguments: dict) -> object:
        """`ai.model.list` — the model ids this key can actually reach."""
        if capability_id == "ai.completion.create":
            return await self._create_completion(arguments)
        if capability_id != "ai.model.list":
            return await super().run_capability(capability_id, arguments)
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await client.get(
                "https://api.anthropic.com/v1/models",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": ANTHROPIC_API_VERSION,
                },
                timeout=10.0,
            )
            response.raise_for_status()
            payload = response.json()
            return {"models": sorted(m["id"] for m in payload.get("data", []) if "id" in m)}
        finally:
            if own_client:
                await client.aclose()

    async def _create_completion(self, arguments: dict[str, Any]) -> dict[str, Any]:
        payload = self._completion_payload(arguments)
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": ANTHROPIC_API_VERSION,
                },
                json=payload,
                timeout=30.0,
            )
            body = self._json_body(response)
            if response.status_code >= 400:
                raise RuntimeError(f"Anthropic returned HTTP {response.status_code}")
            content = body.get("content")
            if not isinstance(content, list):
                raise TypeError("Anthropic returned no completion content")
            text = "".join(
                block.get("text", "")
                for block in content
                if isinstance(block, dict) and block.get("type") == "text"
            )
            if not text:
                raise RuntimeError("Anthropic returned no text completion")
            return {
                "provider": IntegrationProvider.ANTHROPIC.value,
                "model": payload["model"],
                "text": text,
                "stop_reason": body.get("stop_reason"),
                "usage": body.get("usage"),
            }
        except httpx.TimeoutException as exc:
            raise RuntimeError("Anthropic completion timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Anthropic completion failed: {type(exc).__name__}") from exc
        finally:
            if own_client:
                await client.aclose()

    @staticmethod
    def _completion_payload(arguments: dict[str, Any]) -> dict[str, Any]:
        model = arguments.get("model")
        if not isinstance(model, str) or not 1 <= len(model.strip()) <= 100:
            raise ValueError("ai.completion.create requires a model")
        messages = arguments.get("messages")
        if not isinstance(messages, list) or not 1 <= len(messages) <= 50:
            raise ValueError("ai.completion.create requires 1-50 messages")
        normalized: list[dict[str, str]] = []
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
                normalized.append({"role": role, "content": content})
        if not normalized:
            raise ValueError("at least one user or assistant message is required")
        if total_bytes > 100_000:
            raise ValueError("message content must be 100000 UTF-8 bytes or fewer")
        max_tokens = arguments.get("max_tokens", 1024)
        if isinstance(max_tokens, bool) or not isinstance(max_tokens, int) or not 1 <= max_tokens <= 8192:
            raise ValueError("max_tokens must be an integer between 1 and 8192")
        payload: dict[str, Any] = {
            "model": model.strip(),
            "max_tokens": max_tokens,
            "messages": normalized,
        }
        if system_parts:
            payload["system"] = "\n\n".join(system_parts)
        temperature = arguments.get("temperature")
        if temperature is not None:
            if isinstance(temperature, bool) or not isinstance(temperature, (int, float)) or not 0 <= temperature <= 1:
                raise ValueError("temperature must be between 0 and 1")
            payload["temperature"] = temperature
        return payload

    @staticmethod
    def _json_body(response: httpx.Response) -> dict[str, Any]:
        try:
            body = response.json()
        except ValueError as exc:
            raise RuntimeError("Anthropic returned a non-JSON response") from exc
        if not isinstance(body, dict):
            raise TypeError("Anthropic returned an invalid response")
        return body

    async def test_connection(self) -> tuple[bool, float | None, str | None]:
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        started = time.perf_counter()
        try:
            response = await client.get(
                "https://api.anthropic.com/v1/models",
                headers={"x-api-key": self.api_key, "anthropic-version": ANTHROPIC_API_VERSION},
                timeout=10.0,
            )
            latency_ms = (time.perf_counter() - started) * 1000
            if response.status_code == 200:
                return True, latency_ms, None
            if response.status_code == 401:
                return False, latency_ms, "Anthropic rejected the API key (HTTP 401)"
            return False, latency_ms, f"Anthropic returned HTTP {response.status_code}"
        except httpx.TimeoutException:
            return False, None, "Connection to Anthropic timed out"
        except httpx.HTTPError as exc:
            return False, None, f"{type(exc).__name__}: {exc}"
        finally:
            if own_client:
                await client.aclose()
