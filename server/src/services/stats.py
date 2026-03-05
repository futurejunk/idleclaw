from __future__ import annotations


class ServerStats:
    """In-memory operational counters for the metrics endpoint."""

    def __init__(self) -> None:
        self.requests_total: int = 0
        self.requests_active: int = 0
        self.requests_errors_total: int = 0
        self.nodes_registered_total: int = 0
