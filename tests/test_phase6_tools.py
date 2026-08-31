import pytest

from app.tools.approvals import InMemoryApprovalStore
from app.tools.audit import InMemoryToolAuditLog
from app.tools.builtin import build_default_registry
from app.tools.executor import ToolExecutor
from app.tools.models import ToolCall
from app.tools.policy import ToolPolicy


def make_executor():
    approvals = InMemoryApprovalStore()
    return ToolExecutor(
        build_default_registry(),
        ToolPolicy(approvals),
        InMemoryToolAuditLog(),
    ), approvals


@pytest.mark.asyncio
async def test_read_tool_runs_without_approval():
    executor, _ = make_executor()
    result = await executor.execute(ToolCall(tool="echo", arguments={"value": "ok"}))
    assert result.success is True
    assert result.output == "ok"


@pytest.mark.asyncio
async def test_write_tool_cannot_self_approve():
    executor, _ = make_executor()
    result = await executor.execute(
        ToolCall(tool="artifact.write", arguments={"name": "x.txt", "content": "hello"})
    )
    assert result.success is False
    assert result.approval_required is True


@pytest.mark.asyncio
async def test_trusted_approval_is_single_use(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_OS_WORKSPACE_ROOT", str(tmp_path))
    monkeypatch.setenv("AGENT_OS_ARTIFACT_ROOT", str(tmp_path / "artifacts"))

    executor, approvals = make_executor()
    grant = await approvals.issue("artifact.write", approved_by="test-user")
    call = ToolCall(tool="artifact.write", arguments={"name": "ok.txt", "content": "safe"})

    first = await executor.execute(call, approval_id=grant.approval_id)
    second = await executor.execute(call, approval_id=grant.approval_id)

    assert first.success is True
    assert second.success is False
    assert second.approval_required is True


@pytest.mark.asyncio
async def test_sensitive_file_read_is_blocked(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_OS_WORKSPACE_ROOT", str(tmp_path))
    (tmp_path / ".env").write_text("SECRET=x")

    executor, _ = make_executor()
    result = await executor.execute(ToolCall(tool="file.read_text", arguments={"path": ".env"}))
    assert result.success is False
    assert "sensitive" in (result.error or "").lower()


@pytest.mark.asyncio
async def test_path_traversal_is_blocked(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_OS_WORKSPACE_ROOT", str(tmp_path))
    monkeypatch.setenv("AGENT_OS_ARTIFACT_ROOT", str(tmp_path / "artifacts"))

    executor, approvals = make_executor()
    grant = await approvals.issue("artifact.write", approved_by="test-user")
    result = await executor.execute(
        ToolCall(
            tool="artifact.write",
            arguments={"name": "../escape.txt", "content": "bad"},
        ),
        approval_id=grant.approval_id,
    )
    assert result.success is False
    assert "escapes artifacts directory" in (result.error or "")


@pytest.mark.asyncio
async def test_executor_threads_correlation_id_into_audit():
    approvals = InMemoryApprovalStore()
    audit = InMemoryToolAuditLog()
    executor = ToolExecutor(build_default_registry(), ToolPolicy(approvals), audit)

    await executor.execute(
        ToolCall(tool="echo", arguments={"value": "ok"}),
        correlation_id="corr-exec-1",
    )
    events = await audit.list()
    assert events[-1]["correlation_id"] == "corr-exec-1"


@pytest.mark.asyncio
async def test_correlation_id_audited_on_denied_execution():
    # A denied write never reaches the handler, but it is still audited — the
    # correlation id has to survive that early-return path too.
    approvals = InMemoryApprovalStore()
    audit = InMemoryToolAuditLog()
    executor = ToolExecutor(build_default_registry(), ToolPolicy(approvals), audit)

    result = await executor.execute(
        ToolCall(tool="artifact.write", arguments={"name": "x.txt", "content": "y"}),
        correlation_id="corr-denied",
    )
    events = await audit.list()
    assert result.success is False
    assert events[-1]["correlation_id"] == "corr-denied"


@pytest.mark.asyncio
async def test_correlation_id_audited_for_unknown_tool():
    approvals = InMemoryApprovalStore()
    audit = InMemoryToolAuditLog()
    executor = ToolExecutor(build_default_registry(), ToolPolicy(approvals), audit)

    await executor.execute(
        ToolCall(tool="does.not.exist", arguments={}),
        correlation_id="corr-missing",
    )
    events = await audit.list()
    assert events[-1]["correlation_id"] == "corr-missing"
