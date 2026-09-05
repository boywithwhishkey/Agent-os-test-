from __future__ import annotations

import time
from typing import Any

import httpx

from app.core.config import settings
from app.integrations.base import CapabilityNotWired, IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult


class StripeAdapter(IntegrationAdapter):
    """Read-only Stripe account, payment, and subscription operations."""

    def __init__(
        self,
        *,
        secret_key: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.secret_key = secret_key or settings.stripe_secret_key or ""
        self._client = client
        if not self.secret_key.strip():
            raise RuntimeError("STRIPE_SECRET_KEY is required")

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            IntegrationProvider.STRIPE,
            request,
            reason="Stripe mutations are disabled; refunds require a separate approved capability.",
        )

    async def run_capability(self, capability_id: str, arguments: dict[str, Any]) -> object:
        if capability_id == "identity.account.read":
            return await self._get("/v1/account")
        if capability_id == "commerce.payment.list":
            return await self._get("/v1/payment_intents", params=self._limit_params(arguments))
        if capability_id == "commerce.subscription.list":
            return await self._get("/v1/subscriptions", params=self._limit_params(arguments))
        raise CapabilityNotWired(f"{type(self).__name__} has no operation for {capability_id}")

    @staticmethod
    def _limit_params(arguments: dict[str, Any]) -> dict[str, str]:
        value = arguments.get("limit", 20)
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 100:
            raise ValueError("limit must be an integer between 1 and 100")
        return {"limit": str(value)}

    async def _get(self, path: str, *, params: dict[str, str] | None = None) -> dict[str, Any]:
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await client.get(
                f"https://api.stripe.com{path}",
                params=params,
                auth=(self.secret_key, ""),
                timeout=10.0,
            )
            try:
                body = response.json()
            except ValueError as exc:
                raise RuntimeError("Stripe returned a non-JSON response") from exc
            if response.status_code >= 400:
                raise RuntimeError(f"Stripe returned HTTP {response.status_code}")
            if not isinstance(body, dict):
                raise TypeError("Stripe returned an invalid response")
            return body
        except httpx.TimeoutException as exc:
            raise RuntimeError("Stripe request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Stripe request failed: {type(exc).__name__}") from exc
        finally:
            if own_client:
                await client.aclose()

    async def test_connection(self) -> tuple[bool, float | None, str | None]:
        started = time.perf_counter()
        try:
            await self.run_capability("identity.account.read", {})
            return True, (time.perf_counter() - started) * 1000, None
        except RuntimeError as exc:
            return False, (time.perf_counter() - started) * 1000, str(exc)
