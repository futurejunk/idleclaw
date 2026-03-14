from __future__ import annotations

import asyncio
import json
import logging
import random
import re
import uuid

from server.src.services.node_connection import create_request_queue, remove_request_queue

logger = logging.getLogger(__name__)

PROBE_TIMEOUT = 30  # seconds

# Test prompt/answer pairs: (prompt, expected_pattern)
PROBE_PAIRS: list[tuple[str, str]] = [
    ("What is 2 + 2? Answer with just the number.", r"\b4\b"),
    ("What is the capital of France? Answer in one word.", r"(?i)\bparis\b"),
    ("Is water wet? Answer yes or no.", r"(?i)\b(yes|no)\b"),
    ("What color is the sky on a clear day? One word.", r"(?i)\bblue\b"),
    ("How many sides does a triangle have? Just the number.", r"\b3\b"),
    ("What planet is closest to the Sun? One word.", r"(?i)\bmercury\b"),
    ("What is 10 minus 7? Answer with just the number.", r"\b3\b"),
]


def validate_probe_response(response_text: str, expected_pattern: str) -> bool:
    """Check if a probe response matches the expected pattern."""
    return bool(re.search(expected_pattern, response_text))


async def probe_node(
    node,
    registry,
    request_queues: dict[str, asyncio.Queue],
    request_node_map: dict[str, str],
) -> bool:
    """Send a test prompt to a node and validate the response.

    Returns True if the probe passed, False otherwise.
    """
    prompt, expected_pattern = random.choice(PROBE_PAIRS)
    request_id = f"probe-{uuid.uuid4()}"

    queue = create_request_queue(request_queues, request_node_map, request_id, node.node_id)

    # Pick the first model the node serves
    if not node.models:
        remove_request_queue(request_queues, request_node_map, request_id)
        return False

    model_name = node.models[0].name

    try:
        await node.websocket.send_text(json.dumps({
            "type": "inference_request",
            "request_id": request_id,
            "ollama_params": {
                "model": model_name,
                "messages": [{"role": "user", "content": prompt}],
                "stream": True,
                "keep_alive": -1,
            },
        }))
    except Exception:
        logger.warning("Failed to send probe to node %s", node.node_id)
        remove_request_queue(request_queues, request_node_map, request_id)
        return False

    # Collect response chunks
    accumulated = ""
    try:
        while True:
            msg = await asyncio.wait_for(queue.get(), timeout=PROBE_TIMEOUT)
            if msg["type"] == "inference_error":
                logger.info("Probe failed (error) for node %s", node.node_id)
                return False
            if msg["type"] == "inference_chunk":
                chunk = msg.get("chunk", {})
                content = chunk.get("message", {}).get("content", "")
                accumulated += content
                if chunk.get("done"):
                    break
    except asyncio.TimeoutError:
        logger.info("Probe timed out for node %s", node.node_id)
        return False
    finally:
        remove_request_queue(request_queues, request_node_map, request_id)
        # Cancel the probe request on the node
        try:
            await node.websocket.send_text(json.dumps({
                "type": "cancel_request",
                "request_id": request_id,
            }))
        except Exception:
            pass

    passed = validate_probe_response(accumulated, expected_pattern)
    if not passed:
        logger.info("Probe failed (pattern) for node %s (response: %.100s)", node.node_id, accumulated)
        return False

    # NLP toxicity check on probe response (if available)
    from server.src.main import content_filter
    if content_filter._toxicity and content_filter._toxicity.available:
        try:
            from server.src.config import settings
            flagged, scores = content_filter._toxicity.check(accumulated, settings.nlp_block_threshold)
            if flagged:
                logger.warning(
                    "Probe response toxic for node %s: %s (response: %.100s)",
                    node.node_id, scores, accumulated,
                )
                return False
        except Exception:
            logger.debug("NLP probe check failed for node %s", node.node_id, exc_info=True)

    logger.info("Probe passed for node %s (response: %.100s)", node.node_id, accumulated)
    return True


async def probe_loop(
    registry,
    request_queues: dict[str, asyncio.Queue],
    request_node_map: dict[str, str],
    interval: int = 300,
) -> None:
    """Background loop that probes a random node at the configured interval."""
    while True:
        await asyncio.sleep(interval)

        nodes = registry.all_nodes()
        if not nodes:
            logger.debug("No nodes connected, skipping probe cycle")
            continue

        node = random.choice(nodes)
        try:
            passed = await probe_node(node, registry, request_queues, request_node_map)
            if passed:
                registry.adjust_reputation(node.node_id, 0.05)
            else:
                registry.adjust_reputation(node.node_id, -0.15)
        except Exception:
            logger.exception("Probe cycle error for node %s", node.node_id)
