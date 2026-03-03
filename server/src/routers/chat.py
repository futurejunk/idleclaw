from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid

from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

from server.src.models.chat import ChatRequest
from server.src.services.node_connection import create_request_queue, remove_request_queue
from server.src.services.router import RequestRouter

logger = logging.getLogger(__name__)

router = APIRouter()

REQUEST_TIMEOUT = 60  # seconds


@router.post("/api/chat")
async def chat(request: ChatRequest):
    from server.src.main import registry, request_queues, request_node_map

    # Find the best node for the requested model
    node = RequestRouter.select_node(registry, request.model)
    if node is None:
        raise HTTPException(status_code=503, detail=f"No nodes available with model {request.model}")

    request_id = str(uuid.uuid4())
    request_start = time.monotonic()
    logger.info("Inference request started", extra={"request_id": request_id, "model": request.model, "node_id": node.node_id})
    queue = create_request_queue(request_queues, request_node_map, request_id, node.node_id)

    # Send inference request to node
    await node.websocket.send_text(json.dumps({
        "type": "inference_request",
        "request_id": request_id,
        "model": request.model,
        "messages": [{"role": m.role, "content": m.content} for m in request.messages],
        "think": request.think,
    }))
    node.active_requests += 1

    chat_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"

    async def event_generator():
        try:
            while True:
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=REQUEST_TIMEOUT)
                except asyncio.TimeoutError:
                    error_chunk = {
                        "id": chat_id,
                        "object": "chat.completion.chunk",
                        "model": request.model,
                        "choices": [{"delta": {"content": "\n\n[Error: request timed out]"}, "index": 0}],
                    }
                    yield {"data": json.dumps(error_chunk)}
                    yield {"data": "[DONE]"}
                    return

                if msg["type"] == "inference_error":
                    error_chunk = {
                        "id": chat_id,
                        "object": "chat.completion.chunk",
                        "model": request.model,
                        "choices": [{"delta": {"content": f"\n\n[Error: {msg.get('error', 'unknown')}]"}, "index": 0}],
                    }
                    yield {"data": json.dumps(error_chunk)}
                    yield {"data": "[DONE]"}
                    return

                if msg["type"] == "inference_chunk":
                    if msg.get("done"):
                        yield {"data": "[DONE]"}
                        return

                    token = msg.get("token", "")
                    if token:
                        delta = {"content": token}
                        if msg.get("thinking"):
                            delta["reasoning"] = True
                        chunk = {
                            "id": chat_id,
                            "object": "chat.completion.chunk",
                            "model": request.model,
                            "choices": [{"delta": delta, "index": 0}],
                        }
                        yield {"data": json.dumps(chunk)}
        finally:
            duration = time.monotonic() - request_start
            logger.info("Inference request completed", extra={"request_id": request_id, "model": request.model, "node_id": node.node_id, "duration_s": round(duration, 2)})
            node.active_requests = max(0, node.active_requests - 1)
            remove_request_queue(request_queues, request_node_map, request_id)
            # Tell node to cancel if still running (client may have disconnected)
            try:
                await node.websocket.send_text(json.dumps({
                    "type": "cancel_request",
                    "request_id": request_id,
                }))
            except Exception:
                pass

    return EventSourceResponse(event_generator())
