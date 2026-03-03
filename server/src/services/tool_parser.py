from __future__ import annotations

import json
import re

# Regex to match <tool_call>...</tool_call> blocks (including across lines)
_TOOL_CALL_PATTERN = re.compile(r"<tool_call>\s*(.*?)\s*</tool_call>", re.DOTALL)


def parse_tool_calls(
    accumulated_content: str,
    done_message: dict | None = None,
) -> list[dict]:
    """Parse tool calls from a completed response.

    Native path: extract tool_calls from the done chunk message.
    Fallback path: scan accumulated content for <tool_call> tags.

    Returns list of dicts with 'name' and 'arguments' keys.
    """
    # Native path: check done_message for structured tool_calls
    if done_message:
        tool_calls = done_message.get("tool_calls")
        if tool_calls:
            return _parse_native_tool_calls(tool_calls)

    # Fallback path: scan content for <tool_call> tags
    return _parse_fallback_tool_calls(accumulated_content)


def _parse_native_tool_calls(tool_calls: list) -> list[dict]:
    """Parse native Ollama tool_calls into a uniform format."""
    results = []
    for tc in tool_calls:
        func = tc.get("function", {})
        name = func.get("name", "")
        arguments = func.get("arguments", {})
        if name:
            results.append({"name": name, "arguments": arguments})
    return results


def _parse_fallback_tool_calls(content: str) -> list[dict]:
    """Parse <tool_call>...</tool_call> tags from content text."""
    results = []
    for match in _TOOL_CALL_PATTERN.finditer(content):
        raw = match.group(1)
        try:
            parsed = json.loads(raw)
            name = parsed.get("name", "")
            arguments = parsed.get("arguments", {})
            if name:
                results.append({"name": name, "arguments": arguments})
        except (json.JSONDecodeError, TypeError):
            continue
    return results


def strip_tool_tags(content: str) -> str:
    """Remove <tool_call>...</tool_call> blocks from content for display."""
    return _TOOL_CALL_PATTERN.sub("", content).strip()
