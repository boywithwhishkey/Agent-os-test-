from __future__ import annotations

import re
import time
from typing import Any
from urllib.parse import urlsplit

import httpx

from app.core.config import settings
from app.integrations.base import CapabilityNotWired, IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult


class ShopifyAdminAdapter(IntegrationAdapter):
    """Governed Shopify Admin GraphQL operations for one configured store."""

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
            reason="Shopify actions must use governed canonical capabilities.",
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
        if capability_id == "commerce.product.create":
            payload = self._product_payload(arguments)
            result = await self._query(
                "mutation productCreate($product: ProductCreateInput!) { "
                "productCreate(product: $product) { "
                "product { id title handle status } "
                "userErrors { field message } } }",
                variables={"product": payload},
            )
            created = result.get("productCreate")
            if not isinstance(created, dict):
                raise TypeError("Shopify returned an invalid productCreate response")
            errors = created.get("userErrors") or []
            if errors:
                messages = [
                    item.get("message", "unknown validation error")
                    for item in errors[:3]
                    if isinstance(item, dict)
                ]
                raise RuntimeError("Shopify product creation was rejected: " + "; ".join(messages))
            return created
        raise CapabilityNotWired(f"{type(self).__name__} has no operation for {capability_id}")

    @staticmethod
    def _product_payload(arguments: dict[str, Any]) -> dict[str, Any]:
        title = arguments.get("title")
        if not isinstance(title, str) or not 1 <= len(title.strip()) <= 255:
            raise ValueError("commerce.product.create requires a title of 255 characters or fewer")
        payload: dict[str, Any] = {"title": title.strip(), "status": "DRAFT"}
        for key, max_length in (("descriptionHtml", 10_000), ("vendor", 255), ("productType", 255)):
            value = arguments.get(key) if key in arguments else arguments.get(_snake_case(key))
            if value is not None:
                if not isinstance(value, str) or len(value) > max_length:
                    raise ValueError(f"{key} must be a string of {max_length} characters or fewer")
                payload[key] = value
        status = arguments.get("status")
        if status is not None:
            if status not in {"ACTIVE", "ARCHIVED", "DRAFT"}:
                raise ValueError("status must be ACTIVE, ARCHIVED, or DRAFT")
            payload["status"] = status
        handle = arguments.get("handle")
        if handle is not None:
            if (
                not isinstance(handle, str)
                or not 1 <= len(handle) <= 255
                or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", handle)
            ):
                raise ValueError("handle must be a lowercase hyphenated identifier")
            payload["handle"] = handle
        tags = arguments.get("tags")
        if tags is not None:
            if (
                not isinstance(tags, list)
                or len(tags) > 20
                or any(not isinstance(tag, str) or not 1 <= len(tag.strip()) <= 100 for tag in tags)
            ):
                raise ValueError("tags must contain at most 20 non-empty values of 100 characters or fewer")
            payload["tags"] = [tag.strip() for tag in tags]
        return payload

    async def _query(self, query: str, *, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await client.post(
                self._endpoint,
                json={"query": query, "variables": variables or {}},
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


def _snake_case(value: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", value).lower()

    async def test_connection(self) -> tuple[bool, float | None, str | None]:
        started = time.perf_counter()
        try:
            await self.run_capability("identity.account.read", {})
            return True, (time.perf_counter() - started) * 1000, None
        except RuntimeError as exc:
            return False, (time.perf_counter() - started) * 1000, str(exc)
