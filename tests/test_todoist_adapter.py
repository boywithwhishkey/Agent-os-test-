from __future__ import annotations

import json

import httpx
import pytest

from app.integrations.todoist import TodoistAdapter


@pytest.mark.anyio
async def test_todoist_task_list_uses_bounded_fixed_endpoint():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/v1/tasks"
        assert request.url.params["limit"] == "2"
        assert request.url.params["project_id"] == "project_1"
        assert request.headers["authorization"] == "Bearer todoist-test"
        return httpx.Response(200, json={"results": [{"id": "task_1"}], "next_cursor": None})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await TodoistAdapter(api_token="todoist-test", client=client).run_capability(
            "productivity.task.list", {"limit": 2, "project_id": "project_1"}
        )

    assert result == {"results": [{"id": "task_1"}], "next_cursor": None}


@pytest.mark.anyio
async def test_todoist_task_create_is_idempotent_and_approval_routable():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/v1/tasks"
        assert request.headers["authorization"] == "Bearer todoist-test"
        assert len(request.headers["x-request-id"]) == 36
        assert json.loads(request.content) == {
            "content": "Buy milk",
            "priority": 2,
            "labels": ["shopping"],
        }
        return httpx.Response(200, json={"id": "task_1", "content": "Buy milk"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await TodoistAdapter(api_token="todoist-test", client=client).run_capability(
            "productivity.task.create",
            {"content": "Buy milk", "priority": 2, "labels": ["shopping"]},
        )

    assert result == {"id": "task_1", "content": "Buy milk"}


def test_todoist_task_create_rejects_unsafe_fields():
    with pytest.raises(ValueError, match="project_id"):
        TodoistAdapter._id("../tasks", "project_id")
    with pytest.raises(ValueError, match="limit"):
        # A token is unnecessary to exercise the pure validation path.
        TodoistAdapter._limit({"limit": 101})


@pytest.mark.anyio
async def test_todoist_test_connection_reports_auth_failure_without_secret():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "unauthorized"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        connected, latency_ms, error = await TodoistAdapter(
            api_token="todoist-test", client=client
        ).test_connection()

    assert connected is False
    assert latency_ms is not None
    assert "401" in (error or "")
    assert "todoist-test" not in (error or "")
