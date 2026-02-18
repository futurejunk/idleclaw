from __future__ import annotations

import asyncio


# Shared dict: request_id -> asyncio.Queue
# Imported and used by main.py (owns the dict) and node_handler.py (pushes chunks)
# chat.py reads from the queue.

def create_request_queue(
    request_queues: dict[str, asyncio.Queue],
    request_node_map: dict[str, str],
    request_id: str,
    node_id: str,
) -> asyncio.Queue:
    queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
    request_queues[request_id] = queue
    request_node_map[request_id] = node_id
    return queue


def remove_request_queue(
    request_queues: dict[str, asyncio.Queue],
    request_node_map: dict[str, str],
    request_id: str,
) -> None:
    request_queues.pop(request_id, None)
    request_node_map.pop(request_id, None)
