from __future__ import annotations

from datetime import UTC, datetime

from server.src.models.chat import ChatRequest
from server.src.models.node import NodeInfo
from server.src.services.tool_registry import ToolRegistry

_BASE_IDENTITY = (
    "You are a helpful assistant running on IdleClaw, a community platform where "
    "people share their idle compute to host open-source AI models. "
    "Be concise and accurate. If you don't know something, say so rather than guessing."
)


def _build_system_prompt() -> str:
    """Compose the server-injected system prompt: identity + current date."""
    date_str = datetime.now(UTC).strftime("%B %-d, %Y")
    return f"{_BASE_IDENTITY}\n\nToday's date is {date_str}."


def build_ollama_params(
    request: ChatRequest,
    node: NodeInfo,
    tool_registry: ToolRegistry | None = None,
) -> dict:
    """Build the complete ollama_params dict from a chat request and node capabilities."""
    capabilities = node.get_model_capabilities(request.model)
    supports_thinking = capabilities.get("thinking", False)
    supports_tools = capabilities.get("tool_calls", False)

    messages = [{"role": m.role, "content": m.content} for m in request.messages]

    # Conversation history cap: keep system prompt + last 20 messages
    MAX_HISTORY = 20
    if len(messages) > MAX_HISTORY:
        # Preserve system message if present
        if messages and messages[0].get("role") == "system":
            messages = [messages[0]] + messages[-(MAX_HISTORY):]
        else:
            messages = messages[-(MAX_HISTORY):]

    # Build composite system prompt: identity + date + thinking hint + tools + user system msg
    system_parts = [_build_system_prompt()]

    # Nudge thinking models to keep reasoning brief
    if request.think and supports_thinking:
        system_parts.append("Keep your internal reasoning brief and focused.")


    # Tool injection for fallback path (non-native models get tools in system prompt)
    if tool_registry and not tool_registry.is_empty() and not supports_tools:
        system_parts.append(tool_registry.get_tools_prompt())

    # Preserve any existing user system message
    if messages and messages[0].get("role") == "system":
        system_parts.append(messages[0]["content"])
        messages[0] = {"role": "system", "content": "\n\n".join(system_parts)}
    else:
        messages.insert(0, {"role": "system", "content": "\n\n".join(system_parts)})

    params = {
        "model": request.model,
        "messages": messages,
        "stream": True,
        "keep_alive": -1,
    }

    # Server-side think fallback: only send think=true if model supports it
    if request.think and supports_thinking:
        params["think"] = True
    else:
        params["think"] = False

    # Native tool path: include tools array for Ollama
    if tool_registry and not tool_registry.is_empty() and supports_tools:
        params["tools"] = tool_registry.get_tools_schema()

    return params
