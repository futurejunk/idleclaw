"""Tests for node probing: response validation and probe cycle behavior."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

from server.src.models.node import ModelInfo, NodeInfo
from server.src.services.node_prober import PROBE_PAIRS, probe_node, validate_probe_response
from server.src.services.registry import NodeRegistry


def _make_node(node_id: str = "test-node") -> NodeInfo:
    ws = MagicMock()
    ws.send_text = AsyncMock()
    return NodeInfo(
        node_id=node_id,
        websocket=ws,
        models=[ModelInfo(name="llama3.2:3b", size=1_000_000)],
        max_concurrent=2,
    )


class TestValidateProbeResponse:
    def test_math_correct(self):
        assert validate_probe_response("The answer is 4.", PROBE_PAIRS[0][1]) is True

    def test_math_wrong(self):
        assert validate_probe_response("The answer is 5.", PROBE_PAIRS[0][1]) is False

    def test_capital_correct(self):
        assert validate_probe_response("Paris", PROBE_PAIRS[1][1]) is True

    def test_capital_case_insensitive(self):
        assert validate_probe_response("PARIS is the capital", PROBE_PAIRS[1][1]) is True

    def test_all_pairs_have_valid_pattern(self):
        """Sanity check: each probe pair has a compilable regex."""
        import re
        for prompt, pattern in PROBE_PAIRS:
            re.compile(pattern)  # should not raise


class TestProbeNode:
    def test_successful_probe(self):
        node = _make_node()
        registry = NodeRegistry()
        registry.add_node(node)
        queues: dict[str, asyncio.Queue] = {}
        node_map: dict[str, str] = {}

        async def fake_send(msg_str):
            msg = json.loads(msg_str)
            if msg["type"] == "inference_request":
                rid = msg["request_id"]
                q = queues.get(rid)
                if q:
                    await q.put({
                        "type": "inference_chunk",
                        "chunk": {"message": {"content": "4"}, "done": False},
                    })
                    await q.put({
                        "type": "inference_chunk",
                        "chunk": {"message": {"content": ""}, "done": True},
                    })

        node.websocket.send_text = fake_send

        result = asyncio.run(probe_node(node, registry, queues, node_map))
        assert isinstance(result, bool)

    def test_probe_error_response(self):
        node = _make_node()
        registry = NodeRegistry()
        registry.add_node(node)
        queues: dict[str, asyncio.Queue] = {}
        node_map: dict[str, str] = {}

        async def fake_send(msg_str):
            msg = json.loads(msg_str)
            if msg["type"] == "inference_request":
                rid = msg["request_id"]
                q = queues.get(rid)
                if q:
                    await q.put({"type": "inference_error", "error": "ollama_unavailable"})

        node.websocket.send_text = fake_send

        result = asyncio.run(probe_node(node, registry, queues, node_map))
        assert result is False

    def test_no_models(self):
        node = _make_node()
        node.models = []
        registry = NodeRegistry()
        registry.add_node(node)
        queues: dict[str, asyncio.Queue] = {}
        node_map: dict[str, str] = {}

        result = asyncio.run(probe_node(node, registry, queues, node_map))
        assert result is False
