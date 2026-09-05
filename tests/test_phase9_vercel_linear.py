from __future__ import annotations

import httpx
import pytest

from app.integrations.linear import LinearAdapter
from app.integrations.vercel import VercelAdapter


@pytest.mark.anyio
async def test_vercel_identity_and_projects_are_read_only() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v2/user":
            return httpx.Response(200, json={"user": {"id": "u1"}})
        return httpx.Response(200, json={"projects": [{"id": "p1"}]})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        adapter = VercelAdapter(api_token="vercel-token", client=client)
        assert (await adapter.run_capability("identity.account.read", {}))["user"]["id"] == "u1"
        projects = await adapter.run_capability("cloud.service.read", {})
    finally:
        await client.aclose()
    assert projects["projects"] == [{"id": "p1"}]


@pytest.mark.anyio
async def test_linear_identity_and_issues_are_fixed_queries() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        body = request.read().decode()
        if "viewer" in body:
            return httpx.Response(200, json={"data": {"viewer": {"id": "u1"}}})
        return httpx.Response(200, json={"data": {"issues": {"nodes": [{"id": "i1"}]}}})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        adapter = LinearAdapter(api_key="linear-token", client=client)
        assert (await adapter.run_capability("identity.account.read", {}))["viewer"]["id"] == "u1"
        issues = await adapter.run_capability("tracker.issue.list", {})
    finally:
        await client.aclose()
    assert issues["issues"]["nodes"] == [{"id": "i1"}]


def test_daily_connectors_require_tokens(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.integrations.vercel.settings.vercel_api_token", None)
    with pytest.raises(RuntimeError, match="VERCEL_API_TOKEN"):
        VercelAdapter()
    monkeypatch.setattr("app.integrations.linear.settings.linear_api_key", None)
    with pytest.raises(RuntimeError, match="LINEAR_API_KEY"):
        LinearAdapter()
