from __future__ import annotations

import json

import httpx
import pytest

from app.integrations.asana import AsanaAdapter


@pytest.mark.anyio
async def test_asana_task_list_is_workspace_scoped():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/1.0/tasks"
        assert request.url.params["workspace"] == "workspace_1"
        assert request.url.params["assignee"] == "me"
        assert request.url.params["limit"] == "2"
        assert request.headers["authorization"] == "Bearer asana-test"
        return httpx.Response(200, json={"data": [{"gid": "task_1", "name": "Ship"}]})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await AsanaAdapter(
            access_token="asana-test", workspace_gid="workspace_1", client=client
        ).run_capability("productivity.task.list", {"limit": 2})

    assert result == {"data": [{"gid": "task_1", "name": "Ship"}]}


@pytest.mark.anyio
async def test_asana_task_create_is_bounded_and_approval_routable():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/1.0/tasks"
        assert json.loads(request.content) == {
            "data": {
                "name": "Ship",
                "workspace": "workspace_1",
                "notes": "Release it",
                "projects": ["project_1"],
                "due_on": "2026-09-07",
            }
        }
        return httpx.Response(201, json={"data": {"gid": "task_1"}})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await AsanaAdapter(
            access_token="asana-test", workspace_gid="workspace_1", client=client
        ).run_capability(
            "productivity.task.create",
            {
                "content": "Ship",
                "description": "Release it",
                "project": "project_1",
                "due_on": "2026-09-07",
            },
        )

    assert result == {"data": {"gid": "task_1"}}


def test_asana_rejects_unsafe_workspace_and_ids():
    with pytest.raises(ValueError, match="WORKSPACE"):
        AsanaAdapter(access_token="asana-test", workspace_gid="../workspace")
    with pytest.raises(ValueError, match="project"):
        AsanaAdapter._validate_gid("../project", "project")


@pytest.mark.anyio
async def test_asana_test_connection_reports_auth_failure_without_secret():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"errors": [{"message": "unauthorized"}]})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        connected, latency_ms, error = await AsanaAdapter(
            access_token="asana-test", workspace_gid="workspace_1", client=client
        ).test_connection()

    assert connected is False
    assert latency_ms is not None
    assert "401" in (error or "")
    assert "asana-test" not in (error or "")
