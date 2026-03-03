from __future__ import annotations

from server.src.models.chat import ChatRequest
from server.src.models.node import NodeInfo
from server.src.services.tool_registry import ToolRegistry


def build_ollama_params(
    request: ChatRequest,
    node: NodeInfo,
    tool_registry: ToolRegistry | None = None,
) -> dict:
    """Build the complete ollama_params dict from a chat request and node capabilities."""
    capabilities = node.get_model_capabilities(request.model)
    supports_thinking = capabilities.get("thinking", False)
    supports_tools = capabilities.get("tool_calls", False)

    params = {
        "model": request.model,
        "messages": [{"role": m.role, "content": m.content} for m in request.messages],
        "stream": True,
        "keep_alive": -1,
    }

    # Server-side think fallback: only send think=true if model supports it
    if request.think and supports_thinking:
        params["think"] = True
    else:
        params["think"] = False

    # Tool injection (skip if no registry or registry is empty)
    if tool_registry and not tool_registry.is_empty():
        if supports_tools:
            # Native path: include tools array for Ollama
            params["tools"] = tool_registry.get_tools_schema()
        else:
            # Fallback path: inject tool descriptions into system message
            tools_prompt = tool_registry.get_tools_prompt()
            _inject_tools_system_prompt(params, tools_prompt)

    return params


def _inject_tools_system_prompt(params: dict, tools_prompt: str) -> None:
    """Prepend tool descriptions to the system message in params."""
    messages = params["messages"]

    # If there's already a system message, prepend tool prompt to it
    if messages and messages[0].get("role") == "system":
        messages[0] = {
            "role": "system",
            "content": tools_prompt + "\n\n" + messages[0]["content"],
        }
    else:
        # Insert a new system message at the beginning
        messages.insert(0, {"role": "system", "content": tools_prompt})
