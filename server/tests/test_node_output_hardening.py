"""Tests for node-output-hardening: tool rate limiting and content tag stripping."""

from __future__ import annotations

import asyncio
import time

from server.src.services.tool_execution import ToolResult, execute_tool_calls
from server.src.services.tool_parser import ContentTagStripper
from server.src.services.tool_rate_limiter import ToolRateLimiter
from server.src.services.tool_registry import ToolDefinition, ToolRegistry


# --- Helpers ---


def _make_registry() -> ToolRegistry:
    async def _dummy_handler(query: str) -> str:
        return f"results for: {query}"

    reg = ToolRegistry()
    reg.register_tool(ToolDefinition(
        name="web_search",
        description="Search the web",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query"},
            },
            "required": ["query"],
        },
        handler=_dummy_handler,
    ))
    return reg


# --- 4.1  Tool calls beyond rate limit return error results ---


class TestToolRateLimiting:
    def test_within_limit(self):
        limiter = ToolRateLimiter(rpm=5)
        for _ in range(5):
            assert limiter.check("node-a") is True

    def test_exceeds_limit(self):
        limiter = ToolRateLimiter(rpm=3)
        for _ in range(3):
            assert limiter.check("node-a") is True
        assert limiter.check("node-a") is False

    def test_rate_limit_in_execution(self):
        """execute_tool_calls returns error when rate limited."""
        reg = _make_registry()
        # Exhaust the global limiter for this node
        limiter = ToolRateLimiter(rpm=1)
        limiter.check("test-node")  # use up the one allowed call

        # Monkey-patch the module-level limiter
        import server.src.services.tool_execution as mod
        original = mod.tool_rate_limiter
        mod.tool_rate_limiter = limiter
        try:
            results = asyncio.run(
                execute_tool_calls(
                    [{"name": "web_search", "arguments": {"query": "hello"}}],
                    reg,
                    node_id="test-node",
                )
            )
            assert len(results) == 1
            assert "rate limit exceeded" in results[0].result
        finally:
            mod.tool_rate_limiter = original


# --- 4.2  Rate limits are independent per node_id ---


class TestRateLimitPerNode:
    def test_independent_nodes(self):
        limiter = ToolRateLimiter(rpm=2)
        assert limiter.check("node-a") is True
        assert limiter.check("node-a") is True
        assert limiter.check("node-a") is False  # node-a exhausted

        # node-b should still be allowed
        assert limiter.check("node-b") is True
        assert limiter.check("node-b") is True
        assert limiter.check("node-b") is False


# --- 4.3  Sliding window correctly expires old entries ---


class TestSlidingWindow:
    def test_expired_entries_freed(self):
        limiter = ToolRateLimiter(rpm=2)
        assert limiter.check("node-a") is True
        assert limiter.check("node-a") is True
        assert limiter.check("node-a") is False

        # Simulate time passing by manipulating the stored timestamps
        limiter._calls["node-a"] = [time.monotonic() - 61.0, time.monotonic() - 61.0]

        # Now calls should be allowed again (old entries expired)
        assert limiter.check("node-a") is True


# --- 4.4  <tool_call> tags are stripped from streamed content ---


class TestContentTagStripper:
    def test_complete_tag_stripped(self):
        s = ContentTagStripper()
        result = s.feed('Hello <tool_call>{"name": "x", "arguments": {}}</tool_call> world')
        result += s.flush()
        assert result == "Hello  world"

    def test_unclosed_tag_stripped(self):
        s = ContentTagStripper()
        result = s.feed('<tool_call>{"name": "x", "arguments": {}}')
        result += s.flush()
        assert result == ""

    def test_multi_chunk_tag(self):
        s = ContentTagStripper()
        r1 = s.feed("Hello <tool_ca")
        r2 = s.feed('ll>{"name": "x", "arguments": {}}</tool_call> world')
        r3 = s.flush()
        assert r1 + r2 + r3 == "Hello  world"


# --- 4.5  Normal content passes through unchanged ---


class TestNormalContent:
    def test_plain_text(self):
        s = ContentTagStripper()
        result = s.feed("The answer is 42")
        result += s.flush()
        assert result == "The answer is 42"

    def test_empty_string(self):
        s = ContentTagStripper()
        result = s.feed("")
        result += s.flush()
        assert result == ""


# --- 4.6  Angle brackets not part of tool_call tags pass through ---


class TestAngleBrackets:
    def test_math_comparison(self):
        s = ContentTagStripper()
        result = s.feed("x < y and a > b")
        result += s.flush()
        assert result == "x < y and a > b"

    def test_html_tags(self):
        s = ContentTagStripper()
        result = s.feed("<div>hello</div>")
        result += s.flush()
        assert result == "<div>hello</div>"

    def test_partial_match_then_mismatch(self):
        """<to... doesn't match <tool_call, should flush."""
        s = ContentTagStripper()
        result = s.feed("<toolbar>test</toolbar>")
        result += s.flush()
        assert result == "<toolbar>test</toolbar>"
