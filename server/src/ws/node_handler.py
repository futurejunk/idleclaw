from __future__ import annotations

import asyncio
import json
import logging

from fastapi import WebSocket, WebSocketDisconnect

from server.src.config import settings
from server.src.models.node import ModelInfo, NodeInfo, detect_capabilities
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
    client_ip = websocket.client.host if websocket.client else "unknown"

    try:
        # Wait for register message
        raw = await asyncio.wait_for(websocket.receive_text(), timeout=REGISTER_TIMEOUT)
        msg = json.loads(raw)

        if msg.get("type") != "register":
            await websocket.close(code=1008, reason="expected register message")
            return

        # Validate node_id
        node_id = msg.get("node_id", "")
        if not node_id or len(node_id) > 64:
            await websocket.close(code=1008, reason="invalid node_id")
            return

        # Validate model list
        raw_models = msg.get("models", [])
        if not raw_models:
            await websocket.close(code=1008, reason="no models provided")
            return
        if len(raw_models) > settings.max_models_per_node:
            await websocket.close(code=1008, reason="too many models")
            return
        for m in raw_models:
            name = m.get("name", "")
            if not name or len(name) > 64:
                await websocket.close(code=1008, reason="invalid model name")
                return

        # Clamp max_concurrent to 1–10
        max_concurrent = msg.get("max_concurrent", 2)
        max_concurrent = max(1, min(10, max_concurrent))

        # Handle re-registration: close old connection if node_id already exists
        # Must happen before IP limit check so reconnecting nodes free their slot first
        existing = registry.get_node(node_id)
        if existing:
            logger.info("Re-registration for node %s, closing old connection", node_id)
            registry.remove_node(node_id)
            try:
                await existing.websocket.close(code=1000, reason="re-registered")
            except Exception:
                pass

        # Handle duplicate by IP+models: a restarted node-agent generates a new UUID
        # but connects from the same IP with the same model set
        incoming_model_names = {m.get("name", "") for m in raw_models}
        duplicate = registry.find_by_ip_and_models(client_ip, incoming_model_names)
        if duplicate:
            logger.info(
                "Duplicate node detected by IP+models, replacing old node",
                extra={"old_node_id": duplicate.node_id, "new_node_id": node_id, "ip": client_ip},
            )
            registry.remove_node(duplicate.node_id)
            try:
                await duplicate.websocket.close(code=1000, reason="re-registered")
            except Exception:
                pass

        # Enforce per-IP node limit
        if not registry.check_ip_limit(client_ip, settings.max_nodes_per_ip):
            await websocket.close(code=1008, reason="too many nodes from this IP")
            return

        ollama_version = msg.get("ollama_version", "")
        models = [
            ModelInfo(name=m["name"], size=m["size"], capabilities=detect_capabilities(m["name"]))
            for m in raw_models
        ]
        node = NodeInfo(
            node_id=node_id,
            websocket=websocket,
            models=models,
            max_concurrent=max_concurrent,
            ip=client_ip,
            ollama_version=ollama_version,
        )
        registry.add_node(node)
        from server.src.main import stats
        stats.nodes_registered_total += 1
        logger.info("Node registered", extra={"node_id": node.node_id, "models": [m.name for m in models], "ip": client_ip})

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
        logger.info("Node disconnected", extra={"node_id": node.node_id if node else "unregistered"})

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
