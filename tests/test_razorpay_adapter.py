from __future__ import annotations

import base64
import json

import httpx
import pytest

from app.integrations.razorpay import RazorpayAdapter


def _basic(key_id: str, secret: str) -> str:
    return "Basic " + base64.b64encode(f"{key_id}:{secret}".encode()).decode()


@pytest.mark.anyio
async def test_razorpay_payment_and_order_reads_use_basic_auth():
    seen: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.url.path)
        assert request.headers["authorization"] == _basic("rzp_test", "secret")
        assert request.url.params["count"] == "2"
        return httpx.Response(200, json={"entity": "collection", "items": []})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        adapter = RazorpayAdapter(key_id="rzp_test", key_secret="secret", client=client)
        payments = await adapter.run_capability("commerce.payment.list", {"limit": 2})
        orders = await adapter.run_capability("commerce.order.list", {"limit": 2})

    assert payments == {"entity": "collection", "items": []}
    assert orders == {"entity": "collection", "items": []}
    assert seen == ["/v1/payments", "/v1/orders"]


@pytest.mark.anyio
async def test_razorpay_refund_requires_receipt_and_posts_fixed_payment_route():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/v1/payments/pay_abc123/refund"
        assert json.loads(request.content) == {
            "amount": 5000,
            "receipt": "refund-123",
            "speed": "normal",
        }
        return httpx.Response(200, json={"id": "rfnd_1", "payment_id": "pay_abc123"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await RazorpayAdapter(
            key_id="rzp_test", key_secret="secret", client=client
        ).run_capability(
            "commerce.refund.create",
            {"payment_id": "pay_abc123", "amount": 5000, "receipt": "refund-123", "speed": "normal"},
        )

    assert result == {"id": "rfnd_1", "payment_id": "pay_abc123"}


def test_razorpay_refund_rejects_unbounded_or_unsafe_inputs():
    with pytest.raises(ValueError, match="payment_id"):
        # Avoid constructing a live adapter; this pure validation path is enough.
        import asyncio

        asyncio.run(RazorpayAdapter._create_refund(RazorpayAdapter.__new__(RazorpayAdapter), {"payment_id": "../pay", "receipt": "r"}))


@pytest.mark.anyio
async def test_razorpay_test_connection_hides_credentials_on_failure():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": {"description": "unauthorized"}})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        connected, latency_ms, error = await RazorpayAdapter(
            key_id="rzp_test", key_secret="secret", client=client
        ).test_connection()

    assert connected is False
    assert latency_ms is not None
    assert "401" in (error or "")
    assert "secret" not in (error or "")
