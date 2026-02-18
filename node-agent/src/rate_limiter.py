from __future__ import annotations

import os
import time

from dotenv import load_dotenv

load_dotenv()


class TokenBucket:
    """Token-bucket rate limiter for inference requests."""

    def __init__(
        self,
        capacity: int | None = None,
        rate: float | None = None,
    ):
        self.capacity = capacity or int(os.getenv("IDLECLAW_RATE_BURST", "10"))
        self.rate = rate or float(os.getenv("IDLECLAW_RATE_LIMIT", "2"))
        self._tokens = float(self.capacity)
        self._last_refill = time.monotonic()

    def consume(self) -> bool:
        """Try to consume one token. Returns True if allowed, False if rate limited."""
        self._refill()
        if self._tokens >= 1.0:
            self._tokens -= 1.0
            return True
        return False

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
        self._last_refill = now
