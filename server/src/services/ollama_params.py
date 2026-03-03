from __future__ import annotations

from server.src.models.chat import ChatRequest
from server.src.models.node import NodeInfo


def build_ollama_params(request: ChatRequest, node: NodeInfo) -> dict:
    """Build the complete ollama_params dict from a chat request and node capabilities."""
    capabilities = node.get_model_capabilities(request.model)
    supports_thinking = capabilities.get("thinking", False)

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

    return params
