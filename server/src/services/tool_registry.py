from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Coroutine


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema
    handler: Callable[..., Coroutine[Any, Any, str]] | None = None
    prompt_description: str = ""


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register_tool(self, tool: ToolDefinition) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        self._tools[tool.name] = tool

    def get_tools_schema(self) -> list[dict]:
        """Return tools in Ollama format for native tool calling."""
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in self._tools.values()
        ]

    def get_tools_prompt(self) -> str:
        """Return tool descriptions for system prompt fallback."""
        if not self._tools:
            return ""
        lines = ["You have access to the following tools:\n"]
        for t in self._tools.values():
            desc = t.prompt_description or t.description
            lines.append(f"- {t.name}: {desc}")
        lines.append(
            "\nTo use a tool, respond with a <tool_call> tag containing JSON with "
            '"name" and "arguments" keys. Example:\n'
            '<tool_call>{"name": "web_search", "arguments": {"query": "your search"}}</tool_call>\n'
            "\nYou may include text before or after the tool call. "
            "After receiving tool results, provide your final answer."
        )
        return "\n".join(lines)

    def get_handler(self, name: str) -> Callable[..., Coroutine[Any, Any, str]] | None:
        tool = self._tools.get(name)
        return tool.handler if tool else None

    def is_empty(self) -> bool:
        return len(self._tools) == 0


# Global registry instance
tool_registry = ToolRegistry()


def _register_web_search() -> None:
    from server.src.services.tools.web_search import web_search_handler

    tool_registry.register_tool(ToolDefinition(
        name="web_search",
        description="Search the web for current information.",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query",
                },
            },
            "required": ["query"],
        },
        handler=web_search_handler,
        prompt_description=(
            "Search the web for current information. "
            "Use when the user asks about recent events, facts you're unsure about, "
            "or anything that benefits from up-to-date information. "
            "Input: {\"query\": \"your search query\"}"
        ),
    ))


_register_web_search()
