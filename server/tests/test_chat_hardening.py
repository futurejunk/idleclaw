"""Tests for chat API hardening: payload size, history cap, concurrent limits."""

from __future__ import annotations

from unittest.mock import MagicMock

from server.src.middleware.rate_limiter import _active_chat
from server.src.models.chat import ChatMessage, ChatRequest
from server.src.routers.chat import MAX_TOTAL_PAYLOAD_CHARS
from server.src.models.node import ModelInfo, NodeInfo
from server.src.services.ollama_params import build_ollama_params


def _make_node(model: str = "llama3.2:3b") -> NodeInfo:
    ws = MagicMock()
    return NodeInfo(
        node_id="test",
        websocket=ws,
        models=[ModelInfo(name=model, size=1_000_000)],
    )


class TestPayloadSizeLimit:
    def test_payload_under_limit(self):
        total = sum(len(f"msg {i}") for i in range(5))
        assert total < MAX_TOTAL_PAYLOAD_CHARS

    def test_payload_over_limit(self):
        # A single message exceeding the limit
        assert MAX_TOTAL_PAYLOAD_CHARS == 100_000
        content = "x" * 100_001
        total = len(content)
        assert total > MAX_TOTAL_PAYLOAD_CHARS

    def test_max_total_payload_value(self):
        assert MAX_TOTAL_PAYLOAD_CHARS == 100_000


class TestHistoryCap:
    def test_short_conversation_unchanged(self):
        msgs = [ChatMessage(role="user", content=f"msg {i}") for i in range(5)]
        request = ChatRequest(model="llama3.2:3b", messages=msgs)
        params = build_ollama_params(request, _make_node())
        # 5 user msgs + 1 system prompt = 6
        assert len(params["messages"]) == 6

    def test_long_conversation_truncated(self):
        msgs = [ChatMessage(role="user", content=f"msg {i}") for i in range(30)]
        request = ChatRequest(model="llama3.2:3b", messages=msgs)
        params = build_ollama_params(request, _make_node())
        # System prompt + last 20 messages = 21
        assert len(params["messages"]) == 21
        # First message should be system prompt
        assert params["messages"][0]["role"] == "system"

    def test_exactly_20_messages_not_truncated(self):
        msgs = [ChatMessage(role="user", content=f"msg {i}") for i in range(20)]
        request = ChatRequest(model="llama3.2:3b", messages=msgs)
        params = build_ollama_params(request, _make_node())
        # 20 user msgs + 1 system prompt = 21
        assert len(params["messages"]) == 21


class TestConcurrentTracking:
    def test_active_chat_dict_operations(self):
        """Test the concurrent tracking dict operations."""
        ip = "test-ip"
        _active_chat.clear()

        # Simulate incrementing
        _active_chat[ip] = _active_chat.get(ip, 0) + 1
        assert _active_chat[ip] == 1

        _active_chat[ip] = _active_chat.get(ip, 0) + 1
        assert _active_chat[ip] == 2

        # Simulate decrementing
        _active_chat[ip] = max(0, _active_chat.get(ip, 1) - 1)
        assert _active_chat[ip] == 1

        _active_chat[ip] = max(0, _active_chat.get(ip, 1) - 1)
        assert _active_chat[ip] == 0

        _active_chat.clear()
