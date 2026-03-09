from __future__ import annotations

import asyncio
import json
import logging
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

# Keys persisted across restarts (cumulative counters only)
_PERSIST_KEYS = ("requests_total", "nodes_registered_total", "requests_errors_total")

SAVE_INTERVAL = 60  # seconds


class ServerStats:
    """In-memory operational counters for the metrics endpoint."""

    def __init__(self) -> None:
        self.requests_total: int = 0
        self.requests_active: int = 0
        self.requests_errors_total: int = 0
        self.nodes_registered_total: int = 0
        self._persistence_task: asyncio.Task | None = None

    def load(self, path: str) -> None:
        """Load persisted counters from a JSON file. Starts at zero if missing or corrupt."""
        p = Path(path)
        if not p.exists():
            return
        try:
            data = json.loads(p.read_text())
            for key in _PERSIST_KEYS:
                if key in data and isinstance(data[key], int):
                    setattr(self, key, data[key])
            logger.info("Loaded stats from %s: %s", path, {k: getattr(self, k) for k in _PERSIST_KEYS})
        except Exception:
            logger.warning("Could not load stats from %s, starting at zero", path)

    def save(self, path: str) -> None:
        """Save cumulative counters atomically (write to temp file, then rename)."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        data = {key: getattr(self, key) for key in _PERSIST_KEYS}
        try:
            fd, tmp = tempfile.mkstemp(dir=p.parent, suffix=".tmp")
            try:
                with open(fd, "w") as f:
                    json.dump(data, f)
                Path(tmp).replace(p)
            except Exception:
                Path(tmp).unlink(missing_ok=True)
                raise
        except Exception:
            logger.warning("Failed to save stats to %s", path, exc_info=True)

    def start_persistence(self, path: str) -> None:
        """Start background task that saves stats every SAVE_INTERVAL seconds."""
        self._persistence_task = asyncio.create_task(self._persistence_loop(path))

    async def stop_persistence(self) -> None:
        """Stop the persistence background task."""
        if self._persistence_task:
            self._persistence_task.cancel()
            try:
                await self._persistence_task
            except asyncio.CancelledError:
                pass

    async def _persistence_loop(self, path: str) -> None:
        while True:
            await asyncio.sleep(SAVE_INTERVAL)
            self.save(path)
