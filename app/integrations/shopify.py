from __future__ import annotations

import time
from typing import Any
from urllib.parse import urlsplit

import httpx

from app.core.config import settings
from app.integrations.base import CapabilityNotWired, IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult


class ShopifyAdminAdapter(IntegrationAdapter):
    """Read-only Shopify Admin GraphQL operations for one configured store."""

    def __init__(
        self,
        *,
        access_token: str | None = None,
        shop_domain: str | None = None,
        api_version: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.access_token = access_token or settings.shopify_admin_access_token or ""
        raw_domain = shop_domain or settings.shopify_shop_domain or ""
        self.shop_domain = self._normalize_domain(raw_domain)
        self.api_version = api_version or settings.shopify_api_version
        self._client = client
        if not self.access_token.strip():
            raise RuntimeError("SHOPIFY_ADMIN_ACCESS_TOKEN is required")
        if not self.shop_domain:
            raise RuntimeError("SHOPIFY_SHOP_DOMAIN is required")

    @staticmethod
    def _normalize_domain(value: str) -> str:
        candidate = value.strip().lower().rstrip("/")
        if "://" in candidate:
            parts = urlsplit(candidate)
            candidate = parts.netloc
        if "/" in candidate or not candidate.endswith(".myshopify.com"):
            return ""
        return candidate

    @property
    def _endpoint(self) -> str:
        return f"https://{self.shop_domain}/admin/api/{self.api_version}/graphql.json"

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            IntegrationProvider.SHOPIFY,
            request,
            reason="Shopify mutations are not enabled; use governed read capabilities.",
        )

    async def run_capability(self, capability_id: str, arguments: dict[str, Any]) -> object:
        if capability_id == "identity.account.read":
            return await self._query("query { shop { id name } }")
        if capability_id == "commerce.product.list":
            return await self._query(
                "query { products(first: 50) { nodes { id title handle status } } }"
            )
        if capability_id == "commerce.order.list":
            return await self._query(
                "query { orders(first: 50, sortKey: CREATED_AT, reverse: true) "
                "{ nodes { id name createdAt displayFinancialStatus } } }"
            )
        raise CapabilityNotWired(f"{type(self).__name__} has no operation for {capability_id}")

    async def _query(self, query: str) -> dict[str, Any]:
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await client.post(
                self._endpoint,
                json={"query": query},
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                },
                timeout=10.0,
            )
            try:
                body = response.json()
            except ValueError as exc:
                raise RuntimeError("Shopify returned a non-JSON response") from exc
            if response.status_code >= 400:
                raise RuntimeError(f"Shopify returned HTTP {response.status_code}")
            if not isinstance(body, dict) or body.get("errors"):
                raise RuntimeError("Shopify GraphQL returned an error")
            data = body.get("data")
            if not isinstance(data, dict):
                raise TypeError("Shopify returned an invalid GraphQL response")
            return data
        except httpx.TimeoutException as exc:
            raise RuntimeError("Shopify request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Shopify request failed: {type(exc).__name__}") from exc
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
