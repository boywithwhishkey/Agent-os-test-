from __future__ import annotations

import re
import time
from typing import Any

import httpx

from app.core.config import settings
from app.integrations.base import CapabilityNotWired, IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult

_BASE_URL = "https://api.razorpay.com/v1"
_PAYMENT_RE = re.compile(r"pay_[A-Za-z0-9]+\Z")


class RazorpayAdapter(IntegrationAdapter):
    """Governed Razorpay payment/order reads and approval-gated refunds."""

    def __init__(
        self,
        *,
        key_id: str | None = None,
        key_secret: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.key_id = key_id or settings.razorpay_key_id or ""
        self.key_secret = key_secret or settings.razorpay_key_secret or ""
        self._client = client
        if not self.key_id.strip():
            raise RuntimeError("RAZORPAY_KEY_ID is required")
        if not self.key_secret.strip():
            raise RuntimeError("RAZORPAY_KEY_SECRET is required")

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            IntegrationProvider.RAZORPAY,
            request,
            reason="Razorpay actions must use governed canonical capabilities.",
        )

    async def run_capability(self, capability_id: str, arguments: dict[str, Any]) -> object:
        if capability_id == "commerce.payment.list":
            return await self._request("GET", "/payments", params={"count": self._limit(arguments)})
        if capability_id == "commerce.order.list":
            return await self._request("GET", "/orders", params={"count": self._limit(arguments)})
        if capability_id == "commerce.refund.create":
            return await self._create_refund(arguments)
        raise CapabilityNotWired(f"{type(self).__name__} has no operation for {capability_id}")

    async def _create_refund(self, arguments: dict[str, Any]) -> object:
        payment_id = arguments.get("payment_id")
        if not isinstance(payment_id, str) or not _PAYMENT_RE.fullmatch(payment_id.strip()):
            raise ValueError("commerce.refund.create requires a valid Razorpay payment_id")
        payload: dict[str, Any] = {}
        amount = arguments.get("amount")
        if amount is not None:
            if isinstance(amount, bool) or not isinstance(amount, int) or not 1 <= amount <= 99_999_999_999:
                raise ValueError("amount must be an integer between 1 and 99999999999")
            payload["amount"] = amount
        receipt = arguments.get("receipt")
        if not isinstance(receipt, str) or not 1 <= len(receipt.strip()) <= 40:
            raise ValueError("commerce.refund.create requires a receipt idempotency key of 40 characters or fewer")
        payload["receipt"] = receipt.strip()
        speed = arguments.get("speed")
        if speed is not None:
            if speed not in {"normal", "optimum"}:
                raise ValueError("speed must be normal or optimum")
            payload["speed"] = speed
        return await self._request("POST", f"/payments/{payment_id.strip()}/refund", json=payload)

    @staticmethod
    def _limit(arguments: dict[str, Any]) -> int:
        value = arguments.get("limit", 20)
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 100:
            raise ValueError("limit must be an integer between 1 and 100")
        return value

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await client.request(
                method,
                f"{_BASE_URL}{path}",
                params=params,
                json=json,
                auth=(self.key_id, self.key_secret),
                headers={"Content-Type": "application/json"},
                timeout=10.0,
            )
            try:
                body = response.json()
            except ValueError as exc:
                raise RuntimeError("Razorpay returned a non-JSON response") from exc
            if response.status_code >= 400:
                raise RuntimeError(f"Razorpay returned HTTP {response.status_code}")
            if not isinstance(body, dict):
                raise TypeError("Razorpay returned an invalid response")
            return body
        except httpx.TimeoutException as exc:
            raise RuntimeError("Razorpay request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Razorpay request failed: {type(exc).__name__}") from exc
        finally:
            if own_client:
                await client.aclose()

    async def test_connection(self) -> tuple[bool, float | None, str | None]:
        started = time.perf_counter()
        try:
            await self._request("GET", "/orders", params={"count": 1})
            return True, (time.perf_counter() - started) * 1000, None
        except RuntimeError as exc:
            return False, (time.perf_counter() - started) * 1000, str(exc)

