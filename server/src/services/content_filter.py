from __future__ import annotations

import re


class ContentFilter:
    """Regex-based content filter for inbound prompts and outbound responses."""

    def __init__(self, inbound_patterns: list[str], outbound_patterns: list[str]) -> None:
        self._inbound = [re.compile(p, re.IGNORECASE) for p in inbound_patterns]
        self._outbound = [re.compile(p, re.IGNORECASE) for p in outbound_patterns]

    def check_inbound(self, messages: list[dict]) -> str | None:
        """Check messages against inbound blocklist.

        Returns the matched pattern string if blocked, None if clean.
        """
        for msg in messages:
            content = msg.get("content", "")
            if not isinstance(content, str):
                continue
            for pattern in self._inbound:
                if pattern.search(content):
                    return pattern.pattern
        return None

    def filter_outbound(self, chunk: str) -> str:
        """Replace matched outbound patterns with [content filtered]."""
        for pattern in self._outbound:
            chunk = pattern.sub("[content filtered]", chunk)
        return chunk
