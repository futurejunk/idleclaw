from __future__ import annotations

import asyncio
import logging
import time

from server.src.models.node import NodeInfo

logger = logging.getLogger(__name__)


class NodeRegistry:
    """In-memory registry of connected node agents."""

    HEARTBEAT_TIMEOUT = 45  # seconds
    EVICTION_INTERVAL = 15  # seconds

    def __init__(self) -> None:
        self._nodes: dict[str, NodeInfo] = {}
        self._ip_node_count: dict[str, int] = {}
        self._eviction_task: asyncio.Task | None = None
        self.shutting_down: bool = False

    def add_node(self, node: NodeInfo) -> None:
        self._nodes[node.node_id] = node
        if node.ip:
            self._ip_node_count[node.ip] = self._ip_node_count.get(node.ip, 0) + 1
        logger.info("Node registered: %s (models: %s)", node.node_id, [m.name for m in node.models])

    def remove_node(self, node_id: str) -> NodeInfo | None:
        node = self._nodes.pop(node_id, None)
        if node:
            if node.ip and node.ip in self._ip_node_count:
                self._ip_node_count[node.ip] -= 1
                if self._ip_node_count[node.ip] <= 0:
                    del self._ip_node_count[node.ip]
            logger.info("Node removed: %s", node_id)
        return node

    def check_ip_limit(self, ip: str, max_nodes_per_ip: int) -> bool:
        """Return True if the IP is within the node limit."""
        return self._ip_node_count.get(ip, 0) < max_nodes_per_ip

    def update_heartbeat(self, node_id: str, active_requests: int) -> None:
        node = self._nodes.get(node_id)
        if node:
            node.last_heartbeat = time.time()
            node.active_requests = active_requests

    def all_nodes(self) -> list[NodeInfo]:
        return list(self._nodes.values())

    def get_node(self, node_id: str) -> NodeInfo | None:
        return self._nodes.get(node_id)

    def find_by_ip_and_models(self, ip: str, model_names: set[str]) -> NodeInfo | None:
        """Find an existing node with the same IP and same set of models."""
        for node in self._nodes.values():
            if node.ip == ip and {m.name for m in node.models} == model_names:
                return node
        return None

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    def start_eviction(self) -> None:
        self._eviction_task = asyncio.create_task(self._eviction_loop())

    async def stop_eviction(self) -> None:
        if self._eviction_task:
            self._eviction_task.cancel()
            try:
                await self._eviction_task
            except asyncio.CancelledError:
                pass

    async def _eviction_loop(self) -> None:
        while True:
            await asyncio.sleep(self.EVICTION_INTERVAL)
            now = time.time()
            stale = [
                nid for nid, node in self._nodes.items()
                if now - node.last_heartbeat > self.HEARTBEAT_TIMEOUT
            ]
            for nid in stale:
                node = self.remove_node(nid)
                if node:
                    logger.warning("Evicting stale node: %s (no heartbeat for %ds)", nid, self.HEARTBEAT_TIMEOUT)
                    try:
                        await node.websocket.close(code=1000, reason="heartbeat timeout")
                    except Exception:
                        pass
