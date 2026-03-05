from __future__ import annotations

import time

from server.src.config import settings


class ToolRateLimiter:
    """In-memory sliding window rate limiter for tool execution, keyed by node_id."""

    def __init__(self, rpm: int) -> None:
        self._rpm = rpm
        self._calls: dict[str, list[float]] = {}

    def check(self, node_id: str) -> bool:
        """Return True if allowed, False if rate-limited."""
        now = time.monotonic()
        window = 60.0

        calls = self._calls.get(node_id, [])
        calls = [t for t in calls if now - t < window]

        if len(calls) >= self._rpm:
            self._calls[node_id] = calls
            return False

        calls.append(now)
        self._calls[node_id] = calls
        return True


tool_rate_limiter = ToolRateLimiter(rpm=settings.tool_rate_limit_rpm)
