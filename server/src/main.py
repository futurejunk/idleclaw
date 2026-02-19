import asyncio
import json
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from server.src.config import settings
from server.src.routers import chat, health, nodes
from server.src.services.registry import NodeRegistry
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

registry = NodeRegistry()
request_queues: dict[str, asyncio.Queue] = {}
request_node_map: dict[str, str] = {}  # request_id -> node_id


@asynccontextmanager
async def lifespan(app: FastAPI):
    health.set_start_time(time.time())
    registry.start_eviction()
    yield
    await registry.stop_eviction()


app = FastAPI(title="IdleClaw", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(chat.router)
app.include_router(nodes.router)


@app.websocket("/ws/node")
async def ws_node(websocket: WebSocket):
    await node_websocket(websocket, registry, request_queues, request_node_map)
