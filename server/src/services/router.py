from __future__ import annotations

import random

from server.src.models.node import NodeInfo
from server.src.services.registry import NodeRegistry


class RequestRouter:
    """Scoring-based node selection for inference routing."""

    LOAD_WEIGHT = 0.7
    AVAILABILITY_WEIGHT = 0.3

    @staticmethod
    def select_node(registry: NodeRegistry, model: str) -> NodeInfo | None:
        """Select the best node for the given model using load-based scoring.

        Returns None if no suitable node is available.
        """
        candidates: list[tuple[float, NodeInfo]] = []

        for node in registry.all_nodes():
            if not node.has_model(model):
                continue
            if node.active_requests >= node.max_concurrent:
                continue

            load_ratio = node.active_requests / node.max_concurrent if node.max_concurrent > 0 else 1.0
            availability_bonus = 1.0 if node.active_requests < node.max_concurrent else 0.0
            score = (1 - load_ratio) * RequestRouter.LOAD_WEIGHT + availability_bonus * RequestRouter.AVAILABILITY_WEIGHT
            candidates.append((score, node))

        if not candidates:
            return None

        # Find max score, collect ties, pick randomly among them
        max_score = max(s for s, _ in candidates)
        best = [n for s, n in candidates if s == max_score]
        return random.choice(best)
