from __future__ import annotations

import re
import time
from typing import Any

import httpx

from app.core.config import settings
from app.integrations.base import CapabilityNotWired, IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult


class StripeAdapter(IntegrationAdapter):
    """Governed Stripe account, commerce reads, and refund operations."""

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
            reason="Stripe actions must use governed canonical capabilities.",
        )

    async def run_capability(self, capability_id: str, arguments: dict[str, Any]) -> object:
        if capability_id == "identity.account.read":
            return await self._get("/v1/account")
        if capability_id == "commerce.payment.list":
            return await self._get("/v1/payment_intents", params=self._limit_params(arguments))
        if capability_id == "commerce.subscription.list":
            return await self._get("/v1/subscriptions", params=self._limit_params(arguments))
        if capability_id == "commerce.refund.create":
            payload, idempotency_key = self._refund_payload(arguments)
            return await self._post("/v1/refunds", data=payload, idempotency_key=idempotency_key)
        raise CapabilityNotWired(f"{type(self).__name__} has no operation for {capability_id}")

    @staticmethod
    def _limit_params(arguments: dict[str, Any]) -> dict[str, str]:
        value = arguments.get("limit", 20)
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 100:
            raise ValueError("limit must be an integer between 1 and 100")
        return {"limit": str(value)}

    @staticmethod
    def _refund_payload(arguments: dict[str, Any]) -> tuple[dict[str, str], str]:
        """Validate the narrow refund surface before calling Stripe.

        Refunds move money and are therefore also gated by the connector broker's
        HIGH_RISK approval. The adapter adds provider-level validation and an
        idempotency key so an approved retry cannot accidentally double-refund.
        """
        payment_intent = arguments.get("payment_intent")
        charge = arguments.get("charge")
        if (payment_intent is None) == (charge is None):
            raise ValueError("commerce.refund.create requires exactly one of payment_intent or charge")

        source_name, source = ("payment_intent", payment_intent) if payment_intent is not None else ("charge", charge)
        if not isinstance(source, str) or not re.fullmatch(r"(?:pi|ch)_[A-Za-z0-9]+", source.strip()):
            raise ValueError(f"{source_name} must be a valid Stripe identifier")

        idempotency_key = arguments.get("idempotency_key")
        if not isinstance(idempotency_key, str) or not 1 <= len(idempotency_key.strip()) <= 255:
            raise ValueError("commerce.refund.create requires an idempotency_key of 255 characters or fewer")

        payload = {source_name: source.strip()}
        amount = arguments.get("amount")
        if amount is not None:
            if isinstance(amount, bool) or not isinstance(amount, int) or not 1 <= amount <= 99_999_999:
                raise ValueError("amount must be an integer between 1 and 99999999")
            payload["amount"] = str(amount)

        reason = arguments.get("reason")
        if reason is not None:
            if reason not in {"duplicate", "fraudulent", "requested_by_customer"}:
                raise ValueError("reason is not a supported Stripe refund reason")
            payload["reason"] = reason

        return payload, idempotency_key.strip()

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

    async def _post(
        self,
        path: str,
        *,
        data: dict[str, str],
        idempotency_key: str,
    ) -> dict[str, Any]:
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await client.post(
                f"https://api.stripe.com{path}",
                data=data,
                headers={"Idempotency-Key": idempotency_key},
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
