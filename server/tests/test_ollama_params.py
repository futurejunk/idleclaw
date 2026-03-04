from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

from server.src.models.chat import ChatMessage, ChatRequest
from server.src.models.node import ModelInfo, NodeInfo, detect_capabilities
from server.src.services.ollama_params import (
    _BASE_IDENTITY,
    _build_system_prompt,
    build_ollama_params,
)
from server.src.services.tool_registry import ToolDefinition, ToolRegistry


def _make_node(model: str = "test-model", capabilities: dict | None = None) -> NodeInfo:
    """Create a NodeInfo with a mock websocket."""
    caps = capabilities or {}
    return NodeInfo(
        node_id="test-node",
        websocket=MagicMock(),
        models=[ModelInfo(name=model, size=1000, capabilities=caps)],
    )


def _make_request(
    model: str = "test-model",
    messages: list[dict] | None = None,
    think: bool = False,
) -> ChatRequest:
    msgs = messages or [{"role": "user", "content": "hello"}]
    return ChatRequest(
        model=model,
        messages=[ChatMessage(**m) for m in msgs],
        think=think,
    )


# --- _build_system_prompt tests ---


def test_build_system_prompt_contains_identity():
    prompt = _build_system_prompt()
    assert _BASE_IDENTITY in prompt


def test_build_system_prompt_contains_date():
    prompt = _build_system_prompt()
    today = datetime.now(UTC)
    # Check the date is in the prompt (e.g., "March 4, 2026")
    assert today.strftime("%B") in prompt
    assert str(today.year) in prompt


def test_build_system_prompt_date_format():
    prompt = _build_system_prompt()
    # Should contain "Today's date is <Month> <day>, <year>."
    assert "Today's date is" in prompt
    today = datetime.now(UTC)
    expected = today.strftime("%B %-d, %Y")
    assert f"Today's date is {expected}." in prompt


# --- build_ollama_params system prompt tests ---


def test_system_prompt_injected_without_tools():
    request = _make_request()
    node = _make_node()
    params = build_ollama_params(request, node)

    system_msg = params["messages"][0]
    assert system_msg["role"] == "system"
    assert _BASE_IDENTITY in system_msg["content"]
    assert "Today's date is" in system_msg["content"]


def test_system_prompt_with_user_system_message():
    request = _make_request(messages=[
        {"role": "system", "content": "You are a pirate."},
        {"role": "user", "content": "hello"},
    ])
    node = _make_node()
    params = build_ollama_params(request, node)

    system_msg = params["messages"][0]
    assert system_msg["role"] == "system"
    assert _BASE_IDENTITY in system_msg["content"]
    assert "You are a pirate." in system_msg["content"]
    # Identity comes before user system message
    assert system_msg["content"].index(_BASE_IDENTITY) < system_msg["content"].index("You are a pirate.")


def test_system_prompt_with_tools_fallback():
    """Non-native tool model: tools appear in system prompt."""
    request = _make_request()
    node = _make_node(capabilities={"tool_calls": False})

    registry = ToolRegistry()
    registry.register_tool(ToolDefinition(
        name="test_tool",
        description="A test tool",
        parameters={"type": "object", "properties": {}},
    ))

    params = build_ollama_params(request, node, tool_registry=registry)

    system_msg = params["messages"][0]
    assert "test_tool" in system_msg["content"]
    assert _BASE_IDENTITY in system_msg["content"]
    assert "tools" not in params  # No native tools array


def test_system_prompt_with_tools_native():
    """Native tool model: tools go in params, not in system prompt."""
    request = _make_request()
    node = _make_node(capabilities={"tool_calls": True})

    registry = ToolRegistry()
    registry.register_tool(ToolDefinition(
        name="test_tool",
        description="A test tool",
        parameters={"type": "object", "properties": {}},
    ))

    params = build_ollama_params(request, node, tool_registry=registry)

    system_msg = params["messages"][0]
    assert "test_tool" not in system_msg["content"]  # Not in system prompt
    assert _BASE_IDENTITY in system_msg["content"]
    assert "tools" in params  # Native tools array present


def test_system_prompt_ordering_with_tools_and_user_msg():
    """Full composition: identity + date + tools + user system msg."""
    request = _make_request(messages=[
        {"role": "system", "content": "Custom instructions."},
        {"role": "user", "content": "hello"},
    ])
    node = _make_node(capabilities={"tool_calls": False})

    registry = ToolRegistry()
    registry.register_tool(ToolDefinition(
        name="test_tool",
        description="A test tool",
        parameters={"type": "object", "properties": {}},
        prompt_description="Test tool for testing",
    ))

    params = build_ollama_params(request, node, tool_registry=registry)

    content = params["messages"][0]["content"]
    identity_pos = content.index(_BASE_IDENTITY)
    date_pos = content.index("Today's date is")
    tools_pos = content.index("test_tool")
    user_pos = content.index("Custom instructions.")

    assert identity_pos < date_pos < tools_pos < user_pos


# --- detect_capabilities tests ---


def test_detect_capabilities_thinking_model():
    caps = detect_capabilities("qwen3:32b")
    assert caps["thinking"] is True
    assert caps["tool_calls"] is True


def test_detect_capabilities_tool_only_model():
    caps = detect_capabilities("llama3.2:3b")
    assert caps["thinking"] is False
    assert caps["tool_calls"] is True


def test_detect_capabilities_unknown_model():
    caps = detect_capabilities("some-unknown-model:7b")
    assert caps["thinking"] is False
    assert caps["tool_calls"] is False
