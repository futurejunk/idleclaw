from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field

from starlette.responses import Response
from starlette.types import ASGIApp, Receive, Scope, Send

from server.src.config import settings

logger = logging.getLogger(__name__)

CLEANUP_INTERVAL = 300  # 5 minutes
STALE_THRESHOLD = 600  # 10 minutes


@dataclass
class Bucket:
    tokens: float
    last_refill: float
    last_access: float = field(default_factory=time.monotonic)


class RateLimiter:
    """In-memory token bucket rate limiter keyed by IP."""

    def __init__(self) -> None:
        self._buckets: dict[str, dict[str, Bucket]] = {}  # ip -> {path_key -> Bucket}
        self._cleanup_task: asyncio.Task | None = None

    def check(self, ip: str, path_key: str, tokens_per_minute: int) -> tuple[bool, float]:
        """Check if a request is allowed. Returns (allowed, retry_after_seconds)."""
        now = time.monotonic()
        ip_buckets = self._buckets.setdefault(ip, {})
        bucket = ip_buckets.get(path_key)

        if bucket is None:
            bucket = Bucket(tokens=tokens_per_minute, last_refill=now)
            ip_buckets[path_key] = bucket

        # Refill tokens based on elapsed time
        elapsed = now - bucket.last_refill
        bucket.tokens = min(tokens_per_minute, bucket.tokens + elapsed * (tokens_per_minute / 60.0))
        bucket.last_refill = now
        bucket.last_access = now

        if bucket.tokens >= 1.0:
            bucket.tokens -= 1.0
            return True, 0.0

        # Not enough tokens — calculate wait time
        retry_after = (1.0 - bucket.tokens) / (tokens_per_minute / 60.0)
        return False, retry_after

    def start_cleanup(self) -> None:
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop_cleanup(self) -> None:
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    async def _cleanup_loop(self) -> None:
        while True:
            await asyncio.sleep(CLEANUP_INTERVAL)
            now = time.monotonic()
            stale_ips = []
            for ip, buckets in self._buckets.items():
                stale_keys = [k for k, b in buckets.items() if now - b.last_access > STALE_THRESHOLD]
                for k in stale_keys:
                    del buckets[k]
                if not buckets:
                    stale_ips.append(ip)
            for ip in stale_ips:
                del self._buckets[ip]
            if stale_ips:
                logger.debug("Rate limiter cleanup: removed %d stale IPs", len(stale_ips))


# Path → (config key for RPM, path_key for bucketing)
_PATH_LIMITS: list[tuple[str, str, str]] = [
    ("/api/chat", "chat", "rate_limit_chat_rpm"),
    ("/ws/node", "ws", "rate_limit_ws_rpm"),
    ("/api/models", "default", "rate_limit_default_rpm"),
    ("/health", "default", "rate_limit_default_rpm"),
    ("/metrics", "default", "rate_limit_default_rpm"),
    ("/admin", "default", "rate_limit_default_rpm"),
]


def _get_limit(path: str) -> tuple[str, int] | None:
    for prefix, path_key, config_attr in _PATH_LIMITS:
        if path == prefix or path.startswith(prefix + "/"):
            return path_key, getattr(settings, config_attr)
    return None


def _get_client_ip(scope: Scope) -> str:
    # Check X-Forwarded-For from trusted reverse proxy (Caddy)
    headers = dict(scope.get("headers", []))
    forwarded = headers.get(b"x-forwarded-for")
    if forwarded:
        # First IP in the chain is the original client
        return forwarded.decode().split(",")[0].strip()
    # Fallback to direct connection
    client = scope.get("client")
    if client:
        return client[0]
    return "unknown"


rate_limiter = RateLimiter()

# Concurrent chat request tracking per IP
_active_chat: dict[str, int] = {}


class RateLimitMiddleware:
    """ASGI middleware that enforces per-IP rate limits."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        limit = _get_limit(path)
        if limit is None:
            await self.app(scope, receive, send)
            return

        path_key, rpm = limit
        ip = _get_client_ip(scope)
        allowed, retry_after = rate_limiter.check(ip, path_key, rpm)

        if not allowed:
            logger.warning("Rate limit exceeded", extra={"ip": ip, "path": path, "retry_after": round(retry_after, 1)})
            if scope["type"] == "websocket":
                response = Response(
                    content=json.dumps({"detail": "Too many requests"}),
                    status_code=429,
                    media_type="application/json",
                    headers={"Retry-After": str(int(retry_after) + 1)},
                )
                await response(scope, receive, send)
            else:
                response = Response(
                    content=json.dumps({"detail": "Too many requests"}),
                    status_code=429,
                    media_type="application/json",
                    headers={"Retry-After": str(int(retry_after) + 1)},
                )
                await response(scope, receive, send)
            return

        # Concurrent chat request limit per IP
        is_chat = path == "/api/chat" or path.startswith("/api/chat/")
        if is_chat:
            active = _active_chat.get(ip, 0)
            if active >= settings.max_concurrent_chat_per_ip:
                logger.warning("Concurrent chat limit exceeded", extra={"ip": ip, "active": active})
                response = Response(
                    content=json.dumps({"detail": "Too many concurrent requests"}),
                    status_code=429,
                    media_type="application/json",
                    headers={"Retry-After": "5"},
                )
                await response(scope, receive, send)
                return
            _active_chat[ip] = active + 1

        try:
            await self.app(scope, receive, send)
        finally:
            if is_chat:
                _active_chat[ip] = max(0, _active_chat.get(ip, 1) - 1)
                if _active_chat.get(ip, 0) == 0:
                    _active_chat.pop(ip, None)
