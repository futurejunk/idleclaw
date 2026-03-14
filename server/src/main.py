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
from server.src.routers import admin, chat, health, metrics, nodes
from server.src.services.registry import NodeRegistry
from server.src.services.stats import ServerStats
from server.src.services.node_prober import probe_loop
from server.src.services.tool_registry import tool_registry
from server.src.services.nlp_classifier import (
    NLPClassifier,
    create_toxicity_classifier,
    create_injection_classifier,
)
from server.src.services.content_filter import ContentFilter
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

    # In production, suppress uvicorn's access logger — Caddy handles access logging
    # and the plain-text access log lines drown out structured app logs in journald
    if settings.environment == "production":
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


setup_logging()

logger = logging.getLogger(__name__)

registry = NodeRegistry()
stats = ServerStats()
request_queues: dict[str, asyncio.Queue] = {}
request_node_map: dict[str, str] = {}  # request_id -> node_id

# NLP classifiers and content filter (initialized at startup)
toxicity_classifier: NLPClassifier | None = None
injection_classifier: NLPClassifier | None = None
content_filter: ContentFilter = ContentFilter(
    settings.inbound_blocklist, settings.outbound_blocklist
)

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
    global toxicity_classifier, injection_classifier, content_filter

    tool_registry.freeze()
    health.set_start_time(time.time())
    stats.load(settings.stats_file)
    stats.start_persistence(settings.stats_file)
    registry.start_eviction()
    rate_limiter.start_cleanup()

    # Initialize NLP classifiers in a thread to avoid blocking startup
    if settings.nlp_enabled:
        loop = asyncio.get_running_loop()
        if settings.nlp_toxicity_enabled:
            try:
                toxicity_classifier = await loop.run_in_executor(
                    None, create_toxicity_classifier, settings.nlp_model_dir
                )
            except Exception:
                logger.warning("Toxicity classifier init failed — continuing without", exc_info=True)
        if settings.nlp_injection_enabled:
            try:
                injection_classifier = await loop.run_in_executor(
                    None, create_injection_classifier, settings.nlp_model_dir
                )
            except Exception:
                logger.warning("Injection classifier init failed — continuing without", exc_info=True)

    # Rebuild content filter with NLP classifiers
    content_filter = ContentFilter(
        settings.inbound_blocklist,
        settings.outbound_blocklist,
        toxicity_classifier=toxicity_classifier,
        injection_classifier=injection_classifier,
        block_threshold=settings.nlp_block_threshold,
        log_threshold=settings.nlp_log_threshold,
    )

    ping_task = asyncio.create_task(_ping_loop())
    probe_task = asyncio.create_task(
        probe_loop(registry, request_queues, request_node_map, settings.probe_interval_seconds)
    )
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
    probe_task.cancel()
    try:
        await probe_task
    except asyncio.CancelledError:
        pass
    ping_task.cancel()
    try:
        await ping_task
    except asyncio.CancelledError:
        pass
    await stats.stop_persistence()
    stats.save(settings.stats_file)
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
app.include_router(admin.router)


@app.websocket("/ws/node")
async def ws_node(websocket: WebSocket):
    await node_websocket(websocket, registry, request_queues, request_node_map)
