import pytest

from app.tools.builtin import build_default_registry
from app.tools.executor import ToolExecutor
from app.tools.models import ToolCall


@pytest.mark.asyncio
async def test_read_tool_runs_without_approval():
    executor = ToolExecutor(build_default_registry())
    result = await executor.execute(ToolCall(tool="echo", arguments={"value": "ok"}))
    assert result.success is True
    assert result.output == "ok"
    assert result.approval_required is False


@pytest.mark.asyncio
async def test_write_tool_requires_approval():
    executor = ToolExecutor(build_default_registry())
    result = await executor.execute(
        ToolCall(
            tool="artifact.write",
            arguments={"name": "phase6.txt", "content": "hello"},
        )
    )
    assert result.success is False
    assert result.approval_required is True


@pytest.mark.asyncio
async def test_approved_write_is_sandboxed(tmp_path, monkeypatch):
    import app.tools.builtin as builtin

    monkeypatch.setattr(builtin, "WORKSPACE_ROOT", tmp_path.resolve())
    monkeypatch.setattr(builtin, "ARTIFACT_ROOT", (tmp_path / "artifacts").resolve())

    executor = ToolExecutor(builtin.build_default_registry())
    result = await executor.execute(
        ToolCall(
            tool="artifact.write",
            arguments={"name": "reports/test.txt", "content": "safe"},
            approved=True,
        )
    )
    assert result.success is True
    assert (tmp_path / "artifacts/reports/test.txt").read_text() == "safe"


@pytest.mark.asyncio
async def test_path_traversal_is_blocked(tmp_path, monkeypatch):
    import app.tools.builtin as builtin

    monkeypatch.setattr(builtin, "WORKSPACE_ROOT", tmp_path.resolve())
    monkeypatch.setattr(builtin, "ARTIFACT_ROOT", (tmp_path / "artifacts").resolve())

    executor = ToolExecutor(builtin.build_default_registry())
    result = await executor.execute(
        ToolCall(
            tool="artifact.write",
            arguments={"name": "../escape.txt", "content": "bad"},
            approved=True,
        )
    )
    assert result.success is False
    assert "escapes artifacts directory" in (result.error or "")
