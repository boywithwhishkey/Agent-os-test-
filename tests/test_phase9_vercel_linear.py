from __future__ import annotations

import json

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
async def test_vercel_deploy_hook_is_fixed_and_supports_explicit_cache_control() -> None:
    seen: dict[str, object] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        seen["query"] = request.url.query.decode()
        seen["authorization"] = request.headers.get("authorization")
        return httpx.Response(200, json={"job": {"id": "job-1", "state": "PENDING"}})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        adapter = VercelAdapter(api_token="vercel-token", client=client)
        adapter.deploy_hook_url = "https://api.vercel.com/v1/integrations/deploy/prj_1/hook_1"
        result = await adapter.run_capability("cloud.deploy.trigger", {"build_cache": False})
    finally:
        await client.aclose()

    assert result == {"job": {"id": "job-1", "state": "PENDING"}}
    assert seen == {
        "method": "POST",
        "path": "/v1/integrations/deploy/prj_1/hook_1",
        "query": "buildCache=false",
        "authorization": None,
    }


@pytest.mark.anyio
async def test_vercel_deploy_hook_rejects_untrusted_urls_and_types() -> None:
    adapter = VercelAdapter(api_token="vercel-token")
    adapter.deploy_hook_url = "https://attacker.example/hook"
    with pytest.raises(RuntimeError, match="valid Vercel deploy hook"):
        adapter._validated_hook_url()
    adapter.deploy_hook_url = "https://api.vercel.com/v1/integrations/deploy/prj_1/hook_1"
    with pytest.raises(TypeError, match="build_cache"):
        await adapter.run_capability("cloud.deploy.trigger", {"build_cache": "false"})


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


@pytest.mark.anyio
async def test_linear_issue_mutations_use_governed_graphql_variables() -> None:
    requests: list[dict[str, object]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content.decode())
        requests.append(payload)
        query = payload["query"]
        if "IssueCreate" in query:
            return httpx.Response(
                200,
                json={
                    "data": {
                        "issueCreate": {
                            "success": True,
                            "issue": {"id": "i2", "identifier": "THY-2", "title": "Ship"},
                        }
                    }
                },
            )
        return httpx.Response(
            200,
            json={
                "data": {
                    "issueUpdate": {
                        "success": True,
                        "issue": {"id": "i2", "identifier": "THY-2", "title": "Shipped"},
                    }
                }
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        adapter = LinearAdapter(api_key="linear-token", client=client)
        created = await adapter.run_capability(
            "tracker.issue.create",
            {
                "team_id": "team-1",
                "title": "Ship",
                "description": "Release it",
                "state_id": "state-1",
            },
        )
        updated = await adapter.run_capability(
            "tracker.issue.update",
            {"issue_id": "THY-2", "title": "Shipped", "description": "Done"},
        )
    finally:
        await client.aclose()

    assert created["issueCreate"]["issue"]["identifier"] == "THY-2"
    assert updated["issueUpdate"]["issue"]["title"] == "Shipped"
    assert requests[0]["variables"] == {
        "input": {
            "teamId": "team-1",
            "title": "Ship",
            "description": "Release it",
            "stateId": "state-1",
        }
    }
    assert requests[1]["variables"] == {
        "id": "THY-2",
        "input": {"title": "Shipped", "description": "Done"},
    }


@pytest.mark.anyio
async def test_linear_issue_mutations_validate_bounded_inputs() -> None:
    adapter = LinearAdapter(api_key="linear-token", client=httpx.AsyncClient())
    try:
        with pytest.raises(ValueError, match="team_id"):
            await adapter.run_capability("tracker.issue.create", {"title": "Missing team"})
        with pytest.raises(ValueError, match="title"):
            await adapter.run_capability("tracker.issue.create", {"team_id": "team-1", "title": ""})
        with pytest.raises(ValueError, match="requires title"):
            await adapter.run_capability("tracker.issue.update", {"issue_id": "THY-1"})
        with pytest.raises(ValueError, match="valid issue_id"):
            await adapter.run_capability("tracker.issue.update", {"issue_id": "bad id", "title": "x"})
    finally:
        await adapter._client.aclose()


def test_daily_connectors_require_tokens(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.integrations.vercel.settings.vercel_api_token", None)
    with pytest.raises(RuntimeError, match="VERCEL_API_TOKEN"):
        VercelAdapter()
    monkeypatch.setattr("app.integrations.linear.settings.linear_api_key", None)
    with pytest.raises(RuntimeError, match="LINEAR_API_KEY"):
        LinearAdapter()
