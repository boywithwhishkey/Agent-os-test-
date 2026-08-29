import time
from dataclasses import dataclass

@dataclass(slots=True)
class CircuitState:
    failures: int = 0
    opened_at: float | None = None

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, recovery_seconds: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_seconds = recovery_seconds
        self._states: dict[str, CircuitState] = {}

    def allow(self, key: str) -> bool:
        state = self._states.setdefault(key, CircuitState())
        if state.opened_at is None:
            return True
        if time.monotonic() - state.opened_at >= self.recovery_seconds:
            self._states[key] = CircuitState()
            return True
        return False

    def success(self, key: str) -> None:
        self._states[key] = CircuitState()

    def failure(self, key: str) -> None:
        state = self._states.setdefault(key, CircuitState())
        state.failures += 1
        if state.failures >= self.failure_threshold:
            state.opened_at = time.monotonic()

    def status(self, key: str) -> dict:
        """Read-only snapshot for display — never mutates breaker state."""
        state = self._states.get(key, CircuitState())
        if state.opened_at is None:
            return {"state": "closed", "failures": state.failures, "recovers_in_seconds": None}
        remaining = max(0.0, self.recovery_seconds - (time.monotonic() - state.opened_at))
        return {
            "state": "open" if remaining > 0 else "closed",
            "failures": state.failures,
            "recovers_in_seconds": remaining if remaining > 0 else None,
        }
