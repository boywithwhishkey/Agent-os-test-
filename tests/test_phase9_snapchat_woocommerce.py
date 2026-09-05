from __future__ import annotations

import httpx
import pytest

from app.integrations.snapchat import SnapchatMarketingAdapter
from app.integrations.woocommerce import WooCommerceAdapter


@pytest.mark.anyio
async def test_snapchat_organization_discovery_is_read_only() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/me/organizations"
        assert request.url.params["with_ad_accounts"] == "true"
        return httpx.Response(200, json={"request_status": "SUCCESS", "organizations": []})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        result = await SnapchatMarketingAdapter(access_token="snap-token", client=client).run_capability(
            "identity.account.read", {}
        )
    finally:
        await client.aclose()
    assert result["request_status"] == "SUCCESS"


@pytest.mark.anyio
async def test_snapchat_lists_ad_accounts_without_enabling_mutations() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "request_status": "SUCCESS",
                "organizations": [
                    {
                        "organization": {"id": "org-1"},
                        "ad_accounts": [{"id": "ad-1", "name": "Demo"}],
                    }
                ],
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        result = await SnapchatMarketingAdapter(access_token="snap-token", client=client).run_capability(
            "ads.account.list", {}
        )
    finally:
        await client.aclose()

    assert result == {
        "provider": "snapchat",
        "ad_accounts": [{"id": "ad-1", "name": "Demo"}],
    }


@pytest.mark.anyio
async def test_woocommerce_lists_products_with_fixed_store_url() -> None:
    seen: list[tuple[str, str]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.url.path, request.url.query.decode()))
        return httpx.Response(200, json=[{"id": 1, "name": "Demo"}])

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        result = await WooCommerceAdapter(
            store_url="https://shop.example",
            consumer_key="ck_test",
            consumer_secret="cs_test",
            client=client,
        ).run_capability("commerce.product.list", {"per_page": 5})
    finally:
        await client.aclose()
    assert result == [{"id": 1, "name": "Demo"}]
    assert seen == [("/wp-json/wc/v3/products", "per_page=5")]


@pytest.mark.anyio
async def test_woocommerce_creates_a_draft_product_with_bounded_payload() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/wp-json/wc/v3/products"
        assert request.headers["content-type"] == "application/json"
        assert request.content == (
            b'{"name":"Demo product","type":"simple","status":"draft",'
            b'"regular_price":"19.99","sku":"DEMO-1","description":"A short description."}'
        )
        return httpx.Response(201, json={"id": 42, "name": "Demo product", "status": "draft"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        result = await WooCommerceAdapter(
            store_url="https://shop.example",
            consumer_key="ck_test",
            consumer_secret="cs_test",
            client=client,
        ).run_capability(
            "commerce.product.create",
            {
                "name": "Demo product",
                "regular_price": "19.99",
                "sku": "DEMO-1",
                "description": "A short description.",
            },
        )
    finally:
        await client.aclose()

    assert result == {"id": 42, "name": "Demo product", "status": "draft"}


def test_woocommerce_product_create_validates_price_and_status() -> None:
    with pytest.raises(ValueError, match="non-negative decimal"):
        WooCommerceAdapter._product_payload({"name": "Demo", "regular_price": "-1"})
    with pytest.raises(ValueError, match="status is unsupported"):
        WooCommerceAdapter._product_payload({"name": "Demo", "status": "live"})


def test_commerce_connectors_require_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.integrations.snapchat.settings.snapchat_access_token", None)
    with pytest.raises(RuntimeError, match="SNAPCHAT_ACCESS_TOKEN"):
        SnapchatMarketingAdapter()
    monkeypatch.setattr("app.integrations.woocommerce.settings.woocommerce_store_url", "http://local")
    with pytest.raises(RuntimeError, match="WOOCOMMERCE_STORE_URL"):
        WooCommerceAdapter()
