from __future__ import annotations

from datetime import UTC, datetime

from app.integrations.mcp.models import MCPCapabilities, MCPServerCreate, MCPServerRecord


class MCPServerStore:
    """In-memory registry of operator-configured MCP servers.

    Process-local by design, like the rest of the integration status
    telemetry in this codebase — see app/integrations/status_store.py.
    """

    def __init__(self) -> None:
        self._servers: dict[str, MCPServerRecord] = {}

    def create(self, payload: MCPServerCreate) -> MCPServerRecord:
        record = MCPServerRecord.from_create(payload)
        self._servers[record.id] = record
        return record

    def list(self) -> list[MCPServerRecord]:
        return list(self._servers.values())

    def get(self, server_id: str) -> MCPServerRecord | None:
        return self._servers.get(server_id)

    def delete(self, server_id: str) -> bool:
        return self._servers.pop(server_id, None) is not None

    def record_check(
        self,
        server_id: str,
        *,
        connected: bool,
        latency_ms: float | None,
        error: str | None,
        capabilities: MCPCapabilities,
    ) -> None:
        record = self._servers.get(server_id)
        if record is None:
            return
        record.connected = connected
        record.last_check = datetime.now(UTC).isoformat()
        record.last_check_latency_ms = latency_ms
        record.last_check_error = error
        record.capabilities = capabilities
