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


def test_commerce_connectors_require_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.integrations.snapchat.settings.snapchat_access_token", None)
    with pytest.raises(RuntimeError, match="SNAPCHAT_ACCESS_TOKEN"):
        SnapchatMarketingAdapter()
    monkeypatch.setattr("app.integrations.woocommerce.settings.woocommerce_store_url", "http://local")
    with pytest.raises(RuntimeError, match="WOOCOMMERCE_STORE_URL"):
        WooCommerceAdapter()
