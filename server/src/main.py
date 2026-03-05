import asyncio
import json
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from server.src.config import settings
from server.src.middleware.rate_limiter import RateLimitMiddleware, rate_limiter
from server.src.routers import chat, health, metrics, nodes
from server.src.services.registry import NodeRegistry
from server.src.services.stats import ServerStats
from server.src.services.tool_registry import tool_registry
from server.src.ws.node_handler import node_websocket


class JSONLogFormatter(logging.Formatter):
    _default_keys = set(logging.LogRecord("", 0, "", 0, None, None, None).__dict__)

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Merge any extra structured fields passed via `extra={...}`
        for key in record.__dict__:
            if key not in self._default_keys and key != "message":
                log_entry[key] = record.__dict__[key]
        return json.dumps(log_entry)


def setup_logging() -> None:
    root = logging.getLogger()
    root.setLevel(settings.log_level.upper())

    handler = logging.StreamHandler()
    if settings.environment == "production":
        handler.setFormatter(JSONLogFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(levelname)s %(message)s"))
    root.handlers = [handler]


setup_logging()

logger = logging.getLogger(__name__)

registry = NodeRegistry()
stats = ServerStats()
request_queues: dict[str, asyncio.Queue] = {}
request_node_map: dict[str, str] = {}  # request_id -> node_id

PING_INTERVAL = 30  # seconds


async def _ping_loop() -> None:
    """Send WebSocket ping frames to all connected nodes every PING_INTERVAL seconds."""
    while True:
        await asyncio.sleep(PING_INTERVAL)
        for node in registry.all_nodes():
            try:
                await node.websocket.send({"type": "websocket.ping", "bytes": b""})
            except Exception:
                logger.debug("Ping failed for node %s", node.node_id)


@asynccontextmanager
async def lifespan(app: FastAPI):
    tool_registry.freeze()
    health.set_start_time(time.time())
    registry.start_eviction()
    rate_limiter.start_cleanup()
    ping_task = asyncio.create_task(_ping_loop())
    yield

    # Graceful shutdown: stop accepting new requests
    registry.shutting_down = True
    logger.info("Shutting down: draining %d in-flight requests...", len(request_queues))

    # Drain in-flight requests up to the configured timeout
    drain_timeout = settings.shutdown_drain_timeout
    for _ in range(drain_timeout):
        if not request_queues:
            break
        await asyncio.sleep(1)

    if request_queues:
        logger.warning("Drain timeout: %d requests still in flight", len(request_queues))

    # Cancel background tasks
    ping_task.cancel()
    try:
        await ping_task
    except asyncio.CancelledError:
        pass
    await rate_limiter.stop_cleanup()
    await registry.stop_eviction()

    # Close all node WebSocket connections
    for node in registry.all_nodes():
        try:
            await node.websocket.close(code=1001, reason="server shutting down")
        except Exception:
            pass
    logger.info("Shutdown complete")


app = FastAPI(title="IdleClaw", lifespan=lifespan)

app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(metrics.router)
app.include_router(chat.router)
app.include_router(nodes.router)


@app.websocket("/ws/node")
async def ws_node(websocket: WebSocket):
    await node_websocket(websocket, registry, request_queues, request_node_map)
