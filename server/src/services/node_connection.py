from __future__ import annotations

import asyncio


# Shared dict: request_id -> asyncio.Queue
# Imported and used by main.py (owns the dict) and node_handler.py (pushes chunks)
# chat.py reads from the queue.

def create_request_queue(request_queues: dict[str, asyncio.Queue], request_id: str) -> asyncio.Queue:
    queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
    request_queues[request_id] = queue
    return queue


def remove_request_queue(request_queues: dict[str, asyncio.Queue], request_id: str) -> None:
    request_queues.pop(request_id, None)
