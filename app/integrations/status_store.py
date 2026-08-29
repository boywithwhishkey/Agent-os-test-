from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(slots=True)
class IntegrationStatusRecord:
    connected: bool | None = None
    last_check: str | None = None
    last_check_latency_ms: float | None = None
    last_check_error: str | None = None
    last_execution: str | None = None
    last_execution_success: bool | None = None


class IntegrationStatusStore:
    """Tracks the last connection check and execution per provider.

    In-memory and process-local by design: this is operational telemetry for
    the current running instance, not durable state that needs to survive a
    restart.
    """

    def __init__(self) -> None:
        self._records: dict[str, IntegrationStatusRecord] = {}

    def get(self, provider: str) -> IntegrationStatusRecord:
        return self._records.setdefault(provider, IntegrationStatusRecord())

    def record_check(
        self, provider: str, *, connected: bool, latency_ms: float | None, error: str | None
    ) -> None:
        record = self.get(provider)
        record.connected = connected
        record.last_check = datetime.now(UTC).isoformat()
        record.last_check_latency_ms = latency_ms
        record.last_check_error = error

    def record_execution(self, provider: str, *, success: bool) -> None:
        record = self.get(provider)
        record.last_execution = datetime.now(UTC).isoformat()
        record.last_execution_success = success
