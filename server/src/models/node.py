from __future__ import annotations

import time

from fastapi import WebSocket
from pydantic import BaseModel


class ModelInfo(BaseModel):
    name: str
    size: int


class NodeInfo:
    """Tracks a connected node agent. Not a Pydantic model because it holds a WebSocket reference."""

    def __init__(
        self,
        node_id: str,
        websocket: WebSocket,
        models: list[ModelInfo],
        max_concurrent: int = 2,
    ):
        self.node_id = node_id
        self.websocket = websocket
        self.models = models
        self.max_concurrent = max_concurrent
        self.last_heartbeat = time.time()
        self.active_requests = 0

    def has_model(self, model_name: str) -> bool:
        return any(m.name == model_name for m in self.models)
