from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from server.src.services.tool_registry import tool_registry

logger = logging.getLogger(__name__)

TOOL_EXECUTION_TIMEOUT = 15  # seconds


@dataclass
class ToolResult:
    name: str
    result: str


async def execute_tool_calls(tool_calls: list[dict]) -> list[ToolResult]:
    """Execute a list of tool calls sequentially. Returns results for each."""
    results = []
    for tc in tool_calls:
        name = tc.get("name", "")
        arguments = tc.get("arguments", {})
        handler = tool_registry.get_handler(name)

        if handler is None:
            results.append(ToolResult(name=name, result=f"Error: Unknown tool '{name}'"))
            continue

        try:
            result = await asyncio.wait_for(handler(**arguments), timeout=TOOL_EXECUTION_TIMEOUT)
            results.append(ToolResult(name=name, result=result))
        except asyncio.TimeoutError:
            logger.error("Tool execution timed out: %s", name)
            results.append(ToolResult(name=name, result=f"Error: Tool '{name}' timed out after {TOOL_EXECUTION_TIMEOUT}s"))
        except Exception as e:
            logger.error("Tool execution error for %s: %s", name, e, exc_info=True)
            results.append(ToolResult(name=name, result=f"Error: Tool '{name}' failed: {e}"))

    return results
