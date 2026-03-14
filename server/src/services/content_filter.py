from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass, field

from server.src.services.nlp_classifier import NLPClassifier

logger = logging.getLogger(__name__)


@dataclass
class FilterResult:
    blocked: bool = False
    reason: str = ""
    nlp_scores: dict[str, float] = field(default_factory=dict)
    matched_label: str = ""


class ContentFilter:
    """Layered content filter: regex + NLP classifiers for inbound/outbound."""

    def __init__(
        self,
        inbound_patterns: list[str],
        outbound_patterns: list[str],
        *,
        toxicity_classifier: NLPClassifier | None = None,
        injection_classifier: NLPClassifier | None = None,
        block_threshold: float = 0.85,
        log_threshold: float = 0.50,
    ) -> None:
        self._inbound = [re.compile(p, re.IGNORECASE) for p in inbound_patterns]
        self._outbound = [re.compile(p, re.IGNORECASE) for p in outbound_patterns]
        self._toxicity = toxicity_classifier
        self._injection = injection_classifier
        self._block_threshold = block_threshold
        self._log_threshold = log_threshold

    def check_inbound(self, messages: list[dict]) -> FilterResult:
        """Check messages with layered pipeline: regex -> injection -> toxicity.

        Short-circuits on first block.
        """
        for msg in messages:
            content = msg.get("content", "")
            if not isinstance(content, str) or not content:
                continue

            # Layer 1: regex blocklist
            for pattern in self._inbound:
                if pattern.search(content):
                    return FilterResult(
                        blocked=True,
                        reason="regex",
                        matched_label=pattern.pattern,
                    )

            # Layer 2: injection classifier
            if self._injection and self._injection.available:
                flagged, scores = self._injection.check(content, self._block_threshold)
                if flagged:
                    return FilterResult(
                        blocked=True,
                        reason="injection",
                        nlp_scores=scores,
                        matched_label="INJECTION",
                    )
                if scores.get("INJECTION", 0) >= self._log_threshold:
                    logger.warning(
                        "Inbound injection borderline",
                        extra={"scores": scores, "classifier": "injection"},
                    )

            # Layer 3: toxicity classifier
            if self._toxicity and self._toxicity.available:
                flagged, scores = self._toxicity.check(content, self._block_threshold)
                if flagged:
                    top_label = max(scores, key=scores.get)
                    return FilterResult(
                        blocked=True,
                        reason="toxicity",
                        nlp_scores=scores,
                        matched_label=top_label,
                    )
                if any(s >= self._log_threshold for s in scores.values()):
                    logger.warning(
                        "Inbound toxicity borderline",
                        extra={"scores": scores, "classifier": "toxicity"},
                    )

        return FilterResult()

    def filter_outbound(self, chunk: str) -> str:
        """Replace matched outbound patterns with [content filtered]."""
        for pattern in self._outbound:
            chunk = pattern.sub("[content filtered]", chunk)
        return chunk

    def classify_outbound(self, text: str) -> FilterResult:
        """Post-stream NLP classification of outbound content (toxicity + injection)."""
        # Truncate for efficiency
        text = text[:2000]

        # Check toxicity
        if self._toxicity and self._toxicity.available:
            flagged, scores = self._toxicity.check(text, self._block_threshold)
            if flagged:
                top_label = max(scores, key=scores.get)
                return FilterResult(
                    blocked=True,
                    reason="outbound_toxicity",
                    nlp_scores=scores,
                    matched_label=top_label,
                )

        # Check injection (detect if node is trying to inject prompts into response)
        if self._injection and self._injection.available:
            flagged, scores = self._injection.check(text, self._block_threshold)
            if flagged:
                return FilterResult(
                    blocked=True,
                    reason="outbound_injection",
                    nlp_scores=scores,
                    matched_label="INJECTION",
                )

        return FilterResult()

    async def classify_outbound_async(self, text: str) -> FilterResult:
        """Async wrapper — runs classify_outbound in a thread executor."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.classify_outbound, text)
