from __future__ import annotations

import asyncio
import json
import logging
import uuid

import websockets

from src import ollama_bridge
from src.rate_limiter import TokenBucket

logger = logging.getLogger(__name__)

HEARTBEAT_INTERVAL = 15  # seconds


class NodeConnection:
    def __init__(self, server_url: str, models: list[dict]):
        self.server_url = server_url
        self.models = models
        self.node_id = str(uuid.uuid4())
        self.active_requests = 0
        self._ws: websockets.ClientConnection | None = None
        self._rate_limiter = TokenBucket()
        self._inference_tasks: dict[str, asyncio.Task] = {}

    async def connect(self) -> None:
        self._ws = await websockets.connect(self.server_url)
        logger.info("Connected to server: %s", self.server_url)

        # Send register
        await self._ws.send(json.dumps({
            "type": "register",
            "node_id": self.node_id,
            "models": self.models,
            "max_concurrent": 2,
        }))

        # Wait for registered ack
        raw = await self._ws.recv()
        msg = json.loads(raw)
        if msg.get("type") != "registered":
            raise RuntimeError(f"Unexpected response: {msg}")
        logger.info("Registered as node %s with %d model(s)", self.node_id, len(self.models))

    async def heartbeat_loop(self) -> None:
        try:
            while True:
                await asyncio.sleep(HEARTBEAT_INTERVAL)
                if self._ws:
                    await self._ws.send(json.dumps({
                        "type": "heartbeat",
                        "node_id": self.node_id,
                        "active_requests": self.active_requests,
                        "available": True,
                    }))
        except websockets.exceptions.ConnectionClosed:
            logger.info("Heartbeat loop: connection closed")
        except Exception as e:
            logger.warning("Heartbeat loop error: %s", e)

    async def listen(self) -> None:
        if not self._ws:
            raise RuntimeError("Not connected")

        try:
            async for raw in self._ws:
                msg = json.loads(raw)
                if msg.get("type") == "inference_request":
                    request_id = msg["request_id"]
                    task = asyncio.create_task(self._handle_inference(msg))
                    self._inference_tasks[request_id] = task
                    task.add_done_callback(lambda _, rid=request_id: self._inference_tasks.pop(rid, None))
                elif msg.get("type") == "cancel_request":
                    request_id = msg.get("request_id")
                    task = self._inference_tasks.get(request_id)
                    if task and not task.done():
                        task.cancel()
                        logger.info("Cancelled inference: %s", request_id)
        except websockets.exceptions.ConnectionClosed:
            logger.info("Listen loop: connection closed")

    async def _handle_inference(self, msg: dict) -> None:
        request_id = msg["request_id"]
        model = msg["model"]
        messages = msg["messages"]
        think = msg.get("think", False)

        if not self._rate_limiter.consume():
            logger.warning("Rate limited request %s", request_id)
            await self._ws.send(json.dumps({
                "type": "inference_error",
                "request_id": request_id,
                "error": "rate limited",
            }))
            return

        if not await ollama_bridge.check_health():
            logger.warning("Ollama unavailable for request %s", request_id)
            await self._ws.send(json.dumps({
                "type": "inference_error",
                "request_id": request_id,
                "error": "Ollama unavailable",
            }))
            return

        self.active_requests += 1
        logger.info("Inference request %s for model %s", request_id, model)

        try:
            async for token_type, token in ollama_bridge.stream_chat(model, messages, think=think):
                chunk = {
                    "type": "inference_chunk",
                    "request_id": request_id,
                    "token": token,
                    "done": False,
                }
                if token_type == "thinking":
                    chunk["thinking"] = True
                await self._ws.send(json.dumps(chunk))

            # Send done
            await self._ws.send(json.dumps({
                "type": "inference_chunk",
                "request_id": request_id,
                "token": "",
                "done": True,
            }))
            logger.info("Inference complete: %s", request_id)

        except asyncio.CancelledError:
            logger.info("Inference cancelled: %s", request_id)

        except Exception as e:
            logger.exception("Inference error for %s", request_id)
            try:
                await self._ws.send(json.dumps({
                    "type": "inference_error",
                    "request_id": request_id,
                    "error": str(e),
                }))
            except Exception:
                pass

        finally:
            self.active_requests = max(0, self.active_requests - 1)
