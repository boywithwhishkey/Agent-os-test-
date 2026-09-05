from __future__ import annotations

import httpx
import pytest

from app.integrations.amazon import AmazonSPAPIAdapter

COMMON = {
    "lwa_client_id": "lwa-client",
    "lwa_client_secret": "lwa-secret",
    "lwa_refresh_token": "Atzr-refresh",
    "aws_access_key_id": "AKIAEXAMPLE",
    "aws_secret_access_key": "aws-secret",
    "region": "na",
}


@pytest.mark.anyio
async def test_amazon_refreshes_lwa_and_signs_sp_api_request() -> None:
    seen: list[tuple[str, str, str]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path, request.headers.get("authorization", "")))
        if request.url.host == "api.amazon.com":
            return httpx.Response(200, json={"access_token": "Atza-access", "expires_in": 3600})
        return httpx.Response(200, json={"payload": [{"marketplace": "IN"}]})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        result = await AmazonSPAPIAdapter(client=client, **COMMON).run_capability(
            "identity.account.read", {}
        )
    finally:
        await client.aclose()

    assert result["payload"] == [{"marketplace": "IN"}]
    assert seen[0][0:2] == ("POST", "/auth/o2/token")
    assert seen[1][0:2] == ("GET", "/sellers/v1/marketplaceParticipations")
    assert seen[1][2].startswith("AWS4-HMAC-SHA256 ")


@pytest.mark.anyio
async def test_amazon_errors_do_not_leak_credentials() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "invalid_client"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(RuntimeError, match="HTTP 401") as exc:
            await AmazonSPAPIAdapter(client=client, **COMMON).run_capability(
                "identity.account.read", {}
            )
    finally:
        await client.aclose()
    assert "lwa-secret" not in str(exc.value)
    assert "Atzr-refresh" not in str(exc.value)


@pytest.mark.anyio
async def test_amazon_order_list_signs_bounded_query_parameters() -> None:
    seen: list[tuple[str, str, str]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path, request.url.query.decode()))
        if request.url.host == "api.amazon.com":
            return httpx.Response(200, json={"access_token": "Atza-access", "expires_in": 3600})
        assert request.headers["authorization"].startswith("AWS4-HMAC-SHA256 ")
        return httpx.Response(200, json={"payload": {"Orders": [{"AmazonOrderId": "123"}]}})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        result = await AmazonSPAPIAdapter(client=client, **COMMON).run_capability(
            "commerce.order.list",
            {
                "marketplace_ids": ["A1PA6795UKMFR9"],
                "created_after": "2026-08-01T00:00:00Z",
                "order_statuses": ["Unshipped", "Shipped"],
            },
        )
    finally:
        await client.aclose()

    assert result["payload"]["Orders"][0]["AmazonOrderId"] == "123"
    assert seen[0][0:2] == ("POST", "/auth/o2/token")
    assert seen[1] == (
        "GET",
        "/orders/v0/orders",
        "MarketplaceIds=A1PA6795UKMFR9&CreatedAfter=2026-08-01T00%3A00%3A00Z&OrderStatuses=Unshipped&OrderStatuses=Shipped",
    )


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        ({"created_after": "2026-08-01T00:00:00Z"}, "marketplace_ids"),
        (
            {"marketplace_ids": ["A1PA6795UKMFR9"], "created_after": "2026-08-01T00:00:00"},
            "timezone",
        ),
        (
            {
                "marketplace_ids": ["A1PA6795UKMFR9"],
                "created_after": "2026-08-01T00:00:00Z",
                "order_statuses": ["Unknown"],
            },
            "unsupported",
        ),
    ],
)
def test_amazon_order_list_arguments_are_validated(
    arguments: dict[str, object], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        AmazonSPAPIAdapter._order_params(arguments)


def test_amazon_requires_all_signing_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.integrations.amazon.settings.amazon_lwa_client_id", None)
    with pytest.raises(RuntimeError, match="AMAZON_LWA_CLIENT_ID"):
        AmazonSPAPIAdapter()
