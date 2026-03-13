"""Tests for node reputation scoring and routing exclusion."""

from __future__ import annotations

from unittest.mock import MagicMock

from server.src.models.node import ModelInfo, NodeInfo
from server.src.services.registry import NodeRegistry
from server.src.services.router import RequestRouter


def _make_node(node_id: str, model: str = "llama3.2:3b", reputation: float = 0.5) -> NodeInfo:
    ws = MagicMock()
    node = NodeInfo(
        node_id=node_id,
        websocket=ws,
        models=[ModelInfo(name=model, size=1_000_000)],
        max_concurrent=2,
    )
    node.reputation = reputation
    return node


class TestAdjustReputation:
    def test_increase_reputation(self):
        reg = NodeRegistry()
        node = _make_node("n1")
        reg.add_node(node)
        reg.adjust_reputation("n1", 0.1)
        assert node.reputation == 0.6

    def test_decrease_reputation(self):
        reg = NodeRegistry()
        node = _make_node("n1")
        reg.add_node(node)
        reg.adjust_reputation("n1", -0.2)
        assert round(node.reputation, 2) == 0.3

    def test_clamp_at_zero(self):
        reg = NodeRegistry()
        node = _make_node("n1", reputation=0.1)
        reg.add_node(node)
        reg.adjust_reputation("n1", -0.5)
        assert node.reputation == 0.0

    def test_clamp_at_one(self):
        reg = NodeRegistry()
        node = _make_node("n1", reputation=0.9)
        reg.add_node(node)
        reg.adjust_reputation("n1", 0.5)
        assert node.reputation == 1.0

    def test_unknown_node_id(self):
        reg = NodeRegistry()
        reg.adjust_reputation("nonexistent", 0.1)  # should not raise


class TestRoutingWithReputation:
    def test_zero_reputation_excluded(self):
        reg = NodeRegistry()
        node = _make_node("n1", reputation=0.0)
        reg.add_node(node)
        result = RequestRouter.select_node(reg, "llama3.2:3b")
        assert result is None

    def test_high_reputation_preferred(self):
        reg = NodeRegistry()
        node_a = _make_node("a", reputation=0.9)
        node_b = _make_node("b", reputation=0.3)
        reg.add_node(node_a)
        reg.add_node(node_b)

        # Run selection many times to verify node_a is consistently preferred
        selections = [RequestRouter.select_node(reg, "llama3.2:3b") for _ in range(100)]
        a_count = sum(1 for s in selections if s and s.node_id == "a")
        # With same load, node A (0.9 rep) should score higher than node B (0.3 rep)
        assert a_count == 100

    def test_load_outweighs_reputation(self):
        reg = NodeRegistry()
        node_a = _make_node("a", reputation=0.9)
        node_a.active_requests = 1  # 50% load
        node_b = _make_node("b", reputation=0.3)
        node_b.active_requests = 0  # 0% load
        reg.add_node(node_a)
        reg.add_node(node_b)

        # Score A: (0.5)*0.5 + 0.9*0.3 + 1.0*0.2 = 0.25 + 0.27 + 0.2 = 0.72
        # Score B: (1.0)*0.5 + 0.3*0.3 + 1.0*0.2 = 0.50 + 0.09 + 0.2 = 0.79
        # Node B should be preferred
        selections = [RequestRouter.select_node(reg, "llama3.2:3b") for _ in range(100)]
        b_count = sum(1 for s in selections if s and s.node_id == "b")
        assert b_count == 100

    def test_default_reputation(self):
        reg = NodeRegistry()
        node = _make_node("n1")
        reg.add_node(node)
        assert node.reputation == 0.5
        result = RequestRouter.select_node(reg, "llama3.2:3b")
        assert result is not None
