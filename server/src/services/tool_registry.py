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
        self._frozen: bool = False

    def freeze(self) -> None:
        """Prevent further tool registration."""
        self._frozen = True

    def register_tool(self, tool: ToolDefinition) -> None:
        if self._frozen:
            raise RuntimeError("Tool registry is frozen")
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

    def validate_arguments(self, name: str, arguments: dict) -> str | None:
        """Return None if valid, error message string if invalid."""
        tool = self._tools.get(name)
        if tool is None:
            return f"unknown tool '{name}'"

        schema = tool.parameters
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        for param in required:
            if param not in arguments:
                return f"missing required argument '{param}'"

        for param in arguments:
            if param not in properties:
                return f"unexpected argument '{param}'"

        type_map = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict,
        }
        for param, value in arguments.items():
            if param in properties:
                expected = properties[param].get("type")
                if expected and expected in type_map:
                    if not isinstance(value, type_map[expected]):
                        return f"argument '{param}' must be a {expected}"

        return None

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
        description=(
            "Search the web for current information. Use this tool when the user asks about "
            "recent news, events, sports scores, software release versions, people, or any "
            "factual question that may have changed after your training cutoff. "
            "Examples: 'Who won the Oscar for best picture?', 'What is the latest Python version?', "
            "'recent news about AI'"
        ),
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
            "Search the web for current information. Use this tool when the user asks about "
            "recent news, events, sports scores, software release versions, people, or any "
            "factual question that may have changed after your training cutoff.\n"
            "Examples: 'Who won the Oscar for best picture?', 'What is the latest Python version?'\n"
            'Input: {"query": "your search query"}'
        ),
    ))


_register_web_search()
