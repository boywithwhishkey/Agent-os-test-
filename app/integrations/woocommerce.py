from __future__ import annotations

import re
import time
from typing import Any
from urllib.parse import urlsplit

import httpx

from app.core.config import settings
from app.integrations.base import CapabilityNotWired, IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult


class WooCommerceAdapter(IntegrationAdapter):
    """Governed WooCommerce REST operations for one configured store."""

    def __init__(
        self,
        *,
        store_url: str | None = None,
        consumer_key: str | None = None,
        consumer_secret: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.store_url = self._normalize_url(store_url or settings.woocommerce_store_url or "")
        self.consumer_key = consumer_key or settings.woocommerce_consumer_key or ""
        self.consumer_secret = consumer_secret or settings.woocommerce_consumer_secret or ""
        self._client = client
        if not self.store_url:
            raise RuntimeError("WOOCOMMERCE_STORE_URL is required")
        if not self.consumer_key.strip():
            raise RuntimeError("WOOCOMMERCE_CONSUMER_KEY is required")
        if not self.consumer_secret.strip():
            raise RuntimeError("WOOCOMMERCE_CONSUMER_SECRET is required")

    @staticmethod
    def _normalize_url(value: str) -> str:
        candidate = value.strip().rstrip("/")
        parts = urlsplit(candidate)
        if parts.scheme != "https" or not parts.hostname or parts.username or parts.password:
            return ""
        return candidate

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            IntegrationProvider.WOOCOMMERCE,
            request,
            reason="WooCommerce actions must use governed canonical capabilities.",
        )

    async def run_capability(self, capability_id: str, arguments: dict[str, Any]) -> object:
        if capability_id == "identity.account.read":
            return await self._get("system_status")
        if capability_id == "commerce.product.list":
            return await self._get("products", params=self._limit_params(arguments))
        if capability_id == "commerce.product.create":
            return await self._post("products", self._product_payload(arguments))
        if capability_id == "commerce.order.list":
            return await self._get("orders", params=self._limit_params(arguments))
        raise CapabilityNotWired(f"{type(self).__name__} has no operation for {capability_id}")

    @staticmethod
    def _limit_params(arguments: dict[str, Any]) -> dict[str, str]:
        value = arguments.get("per_page", 20)
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 100:
            raise ValueError("per_page must be an integer between 1 and 100")
        return {"per_page": str(value)}

    @staticmethod
    def _product_payload(arguments: dict[str, Any]) -> dict[str, Any]:
        name = arguments.get("name")
        if not isinstance(name, str) or not name.strip() or len(name.strip()) > 200:
            raise ValueError("commerce.product.create requires a name of 200 characters or fewer")
        product_type = arguments.get("type", "simple")
        if product_type not in {"simple", "grouped", "external", "variable"}:
            raise ValueError("commerce.product.create type is unsupported")
        status = arguments.get("status", "draft")
        if status not in {"draft", "pending", "private", "publish"}:
            raise ValueError("commerce.product.create status is unsupported")
        payload: dict[str, Any] = {
            "name": name.strip(),
            "type": product_type,
            "status": status,
        }
        regular_price = arguments.get("regular_price")
        if regular_price is not None:
            if (
                not isinstance(regular_price, str)
                or not re.fullmatch(r"\d{1,9}(?:\.\d{1,2})?", regular_price.strip())
            ):
                raise ValueError("regular_price must be a non-negative decimal string")
            payload["regular_price"] = regular_price.strip()
        sku = arguments.get("sku")
        if sku is not None:
            if not isinstance(sku, str) or len(sku.strip()) > 100:
                raise ValueError("sku must be 100 characters or fewer")
            payload["sku"] = sku.strip()
        description = arguments.get("description")
        if description is not None:
            if not isinstance(description, str) or len(description) > 10000:
                raise ValueError("description must be 10000 characters or fewer")
            payload["description"] = description
        return payload

    async def _get(self, resource: str, *, params: dict[str, str] | None = None) -> Any:
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await client.get(
                f"{self.store_url}/wp-json/wc/v3/{resource}",
                params=params,
                auth=(self.consumer_key, self.consumer_secret),
                timeout=10.0,
            )
            try:
                body = response.json()
            except ValueError as exc:
                raise RuntimeError("WooCommerce returned a non-JSON response") from exc
            if response.status_code >= 400:
                raise RuntimeError(f"WooCommerce returned HTTP {response.status_code}")
            return body
        except httpx.TimeoutException as exc:
            raise RuntimeError("WooCommerce request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"WooCommerce request failed: {type(exc).__name__}") from exc
        finally:
            if own_client:
                await client.aclose()

    async def _post(self, resource: str, payload: dict[str, Any]) -> Any:
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await client.post(
                f"{self.store_url}/wp-json/wc/v3/{resource}",
                json=payload,
                auth=(self.consumer_key, self.consumer_secret),
                timeout=10.0,
            )
            try:
                body = response.json()
            except ValueError as exc:
                raise RuntimeError("WooCommerce returned a non-JSON response") from exc
            if response.status_code >= 400:
                raise RuntimeError(f"WooCommerce returned HTTP {response.status_code}")
            return body
        except httpx.TimeoutException as exc:
            raise RuntimeError("WooCommerce request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"WooCommerce request failed: {type(exc).__name__}") from exc
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
