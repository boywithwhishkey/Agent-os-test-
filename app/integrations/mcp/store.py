from __future__ import annotations

from datetime import UTC, datetime

from app.core.tenant import get_current_tenant
from app.integrations.mcp.models import MCPCapabilities, MCPServerCreate, MCPServerRecord


class MCPServerStore:
    """In-memory registry of operator-configured MCP servers.

    Process-local by design, like the rest of the integration status
    telemetry in this codebase — see app/integrations/status_store.py.
    """

    def __init__(self, *, tenant_id: str = "operator") -> None:
        tenant = tenant_id.strip()
        if not tenant:
            raise ValueError("MCP tenant id must be non-empty")
        self._tenant_id = tenant
        self._servers: dict[tuple[str, str], MCPServerRecord] = {}

    def _key(self, server_id: str) -> tuple[str, str]:
        return get_current_tenant(self._tenant_id), server_id

    def create(self, payload: MCPServerCreate) -> MCPServerRecord:
        record = MCPServerRecord.from_create(payload)
        self._servers[self._key(record.id)] = record
        return record

    def list(self) -> list[MCPServerRecord]:
        tenant_id = get_current_tenant(self._tenant_id)
        return [record for (record_tenant, _), record in self._servers.items() if record_tenant == tenant_id]

    def get(self, server_id: str) -> MCPServerRecord | None:
        return self._servers.get(self._key(server_id))

    def delete(self, server_id: str) -> bool:
        return self._servers.pop(self._key(server_id), None) is not None

    def record_check(
        self,
        server_id: str,
        *,
        connected: bool,
        latency_ms: float | None,
        error: str | None,
        capabilities: MCPCapabilities,
    ) -> None:
        record = self._servers.get(self._key(server_id))
        if record is None:
            return
        record.connected = connected
        record.last_check = datetime.now(UTC).isoformat()
        record.last_check_latency_ms = latency_ms
        record.last_check_error = error
        record.capabilities = capabilities
