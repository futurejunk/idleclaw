from __future__ import annotations

import time

from fastapi import WebSocket
from pydantic import BaseModel


THINKING_MODEL_PATTERNS = ("qwen3",)

TOOL_CALL_MODEL_PATTERNS = (
    "qwen3", "llama3.1", "llama3.2", "llama3.3", "mistral", "ministral",
    "granite4", "devstral", "gpt-oss", "qwen3.5", "functiongemma",
)


def detect_capabilities(model_name: str) -> dict:
    """Detect model capabilities from name heuristics."""
    name_lower = model_name.lower()
    return {
        "thinking": any(p in name_lower for p in THINKING_MODEL_PATTERNS),
        "tool_calls": any(p in name_lower for p in TOOL_CALL_MODEL_PATTERNS),
    }


class ModelInfo(BaseModel):
    name: str
    size: int
    capabilities: dict = {}


class NodeInfo:
    """Tracks a connected node agent. Not a Pydantic model because it holds a WebSocket reference."""

    def __init__(
        self,
        node_id: str,
        websocket: WebSocket,
        models: list[ModelInfo],
        max_concurrent: int = 2,
        ip: str = "",
        ollama_version: str = "",
    ):
        self.node_id = node_id
        self.websocket = websocket
        self.models = models
        self.max_concurrent = max_concurrent
        self.ip = ip
        self.ollama_version = ollama_version
        self.connected_at = time.time()
        self.last_heartbeat = time.time()
        self.active_requests = 0

    def has_model(self, model_name: str) -> bool:
        return any(m.name == model_name for m in self.models)

    def get_model_capabilities(self, model_name: str) -> dict:
        """Get capabilities for a specific model."""
        for m in self.models:
            if m.name == model_name:
                return m.capabilities
        return {}
