from __future__ import annotations

import asyncio
import json
import logging

from fastapi import WebSocket, WebSocketDisconnect

from server.src.models.node import ModelInfo, NodeInfo
from server.src.services.registry import NodeRegistry

logger = logging.getLogger(__name__)

REGISTER_TIMEOUT = 10  # seconds


async def node_websocket(
    websocket: WebSocket,
    registry: NodeRegistry,
    request_queues: dict[str, asyncio.Queue],
    request_node_map: dict[str, str],
) -> None:
    await websocket.accept()
    node: NodeInfo | None = None

    try:
        # Wait for register message
        raw = await asyncio.wait_for(websocket.receive_text(), timeout=REGISTER_TIMEOUT)
        msg = json.loads(raw)

        if msg.get("type") != "register":
            await websocket.close(code=1008, reason="expected register message")
            return

        models = [ModelInfo(name=m["name"], size=m["size"]) for m in msg.get("models", [])]
        node = NodeInfo(
            node_id=msg["node_id"],
            websocket=websocket,
            models=models,
            max_concurrent=msg.get("max_concurrent", 2),
        )
        registry.add_node(node)

        await websocket.send_text(json.dumps({"type": "registered", "node_id": node.node_id}))

        # Message loop
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            msg_type = msg.get("type")

            if msg_type == "heartbeat":
                registry.update_heartbeat(
                    node_id=msg["node_id"],
                    active_requests=msg.get("active_requests", 0),
                )

            elif msg_type == "inference_chunk":
                request_id = msg.get("request_id")
                queue = request_queues.get(request_id)
                if queue:
                    await queue.put(msg)

            elif msg_type == "inference_error":
                request_id = msg.get("request_id")
                queue = request_queues.get(request_id)
                if queue:
                    await queue.put(msg)

    except asyncio.TimeoutError:
        logger.warning("Node did not register within %ds, closing connection", REGISTER_TIMEOUT)
        await websocket.close(code=1008, reason="registration timeout")

    except WebSocketDisconnect:
        logger.info("Node disconnected: %s", node.node_id if node else "unregistered")

    except Exception:
        logger.exception("Error in node WebSocket handler")

    finally:
        if node:
            registry.remove_node(node.node_id)
            # Send error only to request queues belonging to this node
            for request_id, owner_node_id in list(request_node_map.items()):
                if owner_node_id == node.node_id:
                    queue = request_queues.get(request_id)
                    if queue:
                        await queue.put({
                            "type": "inference_error",
                            "request_id": request_id,
                            "error": f"Node {node.node_id} disconnected",
                        })
                    request_node_map.pop(request_id, None)
