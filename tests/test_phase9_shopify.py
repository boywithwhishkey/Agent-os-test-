from __future__ import annotations

import httpx
import pytest

from app.integrations.shopify import ShopifyAdminAdapter

TOKEN = "shpat_secret_token"
DOMAIN = "demo.myshopify.com"


@pytest.mark.anyio
async def test_shopify_identity_and_products_use_fixed_graphql_queries() -> None:
    seen: list[tuple[str, str]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        body = request.read().decode()
        seen.append((str(request.url), body))
        if "products" in body:
            return httpx.Response(200, json={"data": {"products": {"nodes": [{"id": "p1"}]}}})
        return httpx.Response(200, json={"data": {"shop": {"id": "s1", "name": "Demo"}}})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        adapter = ShopifyAdminAdapter(
            access_token=TOKEN, shop_domain=DOMAIN, api_version="2025-07", client=client
        )
        assert (await adapter.run_capability("identity.account.read", {}))["shop"]["id"] == "s1"
        products = await adapter.run_capability("commerce.product.list", {})
    finally:
        await client.aclose()

    assert products["products"]["nodes"] == [{"id": "p1"}]
    assert seen[0][0] == "https://demo.myshopify.com/admin/api/2025-07/graphql.json"
    assert "products" in seen[1][1]


@pytest.mark.anyio
async def test_shopify_graphql_errors_do_not_leak_token() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"errors": [{"message": "unauthorized"}]})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(RuntimeError, match="HTTP 401") as exc:
            await ShopifyAdminAdapter(access_token=TOKEN, shop_domain=DOMAIN, client=client).run_capability(
                "identity.account.read", {}
            )
    finally:
        await client.aclose()
    assert TOKEN not in str(exc.value)


def test_shopify_requires_valid_domain_and_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.integrations.shopify.settings.shopify_admin_access_token", None)
    with pytest.raises(RuntimeError, match="SHOPIFY_ADMIN_ACCESS_TOKEN"):
        ShopifyAdminAdapter()
    monkeypatch.setattr("app.integrations.shopify.settings.shopify_admin_access_token", TOKEN)
    monkeypatch.setattr("app.integrations.shopify.settings.shopify_shop_domain", "evil.example")
    with pytest.raises(RuntimeError, match="SHOPIFY_SHOP_DOMAIN"):
        ShopifyAdminAdapter()
