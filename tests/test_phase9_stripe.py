from __future__ import annotations

import httpx
import pytest

from app.integrations.stripe import StripeAdapter

KEY = "sk_test_secret_key"


@pytest.mark.anyio
async def test_stripe_identity_and_payment_list_use_read_only_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.url.path, request.url.query.decode()))
        if request.url.path.endswith("/account"):
            return httpx.Response(200, json={"id": "acct_1", "livemode": False})
        return httpx.Response(200, json={"object": "list", "data": [{"id": "pi_1"}]})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        adapter = StripeAdapter(secret_key=KEY, client=client)
        assert (await adapter.run_capability("identity.account.read", {}))["id"] == "acct_1"
        payments = await adapter.run_capability("commerce.payment.list", {"limit": 5})
    finally:
        await client.aclose()
    assert payments["data"] == [{"id": "pi_1"}]
    assert seen == [
        ("/v1/account", ""),
        ("/v1/payment_intents", "limit=5"),
    ]


@pytest.mark.anyio
async def test_stripe_auth_errors_do_not_leak_secret_key() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": {"message": "bad key"}})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(RuntimeError, match="HTTP 401") as exc:
            await StripeAdapter(secret_key=KEY, client=client).run_capability(
                "identity.account.read", {}
            )
    finally:
        await client.aclose()
    assert KEY not in str(exc.value)


def test_stripe_requires_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.integrations.stripe.settings.stripe_secret_key", None)
    with pytest.raises(RuntimeError, match="STRIPE_SECRET_KEY"):
        StripeAdapter()
