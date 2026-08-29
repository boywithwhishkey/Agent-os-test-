import time
from collections import deque

class SlidingWindowRateLimiter:
    def __init__(self, limit: int = 60, window_seconds: float = 60.0):
        self.limit = limit
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = {}

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        events = self._events.setdefault(key, deque())
        cutoff = now - self.window_seconds
        while events and events[0] <= cutoff:
            events.popleft()
        if len(events) >= self.limit:
            return False
        events.append(now)
        return True

    def usage(self, key: str) -> dict:
        """Read-only snapshot for display — never consumes a slot."""
        now = time.monotonic()
        events = self._events.get(key, deque())
        cutoff = now - self.window_seconds
        used = sum(1 for e in events if e > cutoff)
        return {"used": used, "limit": self.limit, "window_seconds": self.window_seconds}
