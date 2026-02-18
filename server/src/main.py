import asyncio
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from server.src.config import settings
from server.src.routers import chat, health
from server.src.services.registry import NodeRegistry
from server.src.ws.node_handler import node_websocket

registry = NodeRegistry()
request_queues: dict[str, asyncio.Queue] = {}


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


@app.websocket("/ws/node")
async def ws_node(websocket: WebSocket):
    await node_websocket(websocket, registry, request_queues)
