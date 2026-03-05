from __future__ import annotations

import json
import re

# Regex to match <tool_call>...</tool_call> blocks (including across lines)
_TOOL_CALL_PATTERN = re.compile(r"<tool_call>\s*(.*?)\s*</tool_call>", re.DOTALL)
# Fallback: match <tool_call> with JSON but no closing tag (common with small models)
_TOOL_CALL_UNCLOSED = re.compile(r"<tool_call>\s*(\{.*)", re.DOTALL)


def parse_tool_calls(
    accumulated_content: str,
    done_message: dict | None = None,
    *,
    native_only: bool = False,
) -> list[dict]:
    """Parse tool calls from a completed response.

    Native path: extract tool_calls from the done chunk message.
    Fallback path: scan accumulated content for <tool_call> tags.
    When native_only=True, skip the fallback regex path entirely.

    Returns list of dicts with 'name' and 'arguments' keys.
    """
    # Native path: check done_message for structured tool_calls
    if done_message:
        tool_calls = done_message.get("tool_calls")
        if tool_calls:
            return _parse_native_tool_calls(tool_calls)

    # Skip regex fallback for native-tool models
    if native_only:
        return []

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
    """Parse <tool_call>...</tool_call> tags from content text.

    Also handles unclosed tags (small models often omit </tool_call>).
    """
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
    # Fallback: try unclosed tags if no closed matches found
    if not results:
        decoder = json.JSONDecoder()
        for match in _TOOL_CALL_UNCLOSED.finditer(content):
            raw = match.group(1).strip()
            try:
                parsed, _ = decoder.raw_decode(raw)
                name = parsed.get("name", "")
                arguments = parsed.get("arguments", {})
                if name:
                    results.append({"name": name, "arguments": arguments})
            except (json.JSONDecodeError, TypeError, ValueError):
                continue
    return results


class ContentTagStripper:
    """Strips <tool_call>...</tool_call> tags from streaming content.

    Handles tags that span multiple chunks by buffering partial matches.
    Only the exact ``<tool_call>`` prefix triggers buffering — other angle
    brackets pass through unchanged.
    """

    _OPEN = "<tool_call>"
    _CLOSE = "</tool_call>"

    def __init__(self) -> None:
        self._buffer = ""
        self._in_tag = False

    def feed(self, text: str) -> str:
        """Process a content chunk. Returns text with tags stripped."""
        result: list[str] = []
        for ch in text:
            if self._in_tag:
                self._buffer += ch
                if self._buffer.endswith(self._CLOSE):
                    self._buffer = ""
                    self._in_tag = False
            elif self._buffer:
                self._buffer += ch
                if self._buffer == self._OPEN:
                    self._in_tag = True
                elif self._buffer != self._OPEN[: len(self._buffer)]:
                    result.append(self._buffer)
                    self._buffer = ""
            elif ch == "<":
                self._buffer = ch
            else:
                result.append(ch)
        return "".join(result)

    def flush(self) -> str:
        """Return any remaining buffered content at end of stream.

        Discards unclosed tags (inside a ``<tool_call>`` that never closed).
        """
        if self._in_tag:
            self._buffer = ""
            self._in_tag = False
            return ""
        out = self._buffer
        self._buffer = ""
        return out


def strip_tool_tags(content: str) -> str:
    """Remove <tool_call>...</tool_call> blocks from content for display."""
    result = _TOOL_CALL_PATTERN.sub("", content)
    result = _TOOL_CALL_UNCLOSED.sub("", result)
    return result.strip()
