from __future__ import annotations

import asyncio
import logging
import os

from dotenv import load_dotenv

from src import ollama_bridge
from src.connection import NodeConnection

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger(__name__)

SERVER_URL = os.getenv("IDLECLAW_SERVER", "ws://localhost:8000/ws/node")


async def main() -> None:
    # Discover local Ollama models
    logger.info("Discovering local Ollama models...")
    try:
        models = await ollama_bridge.list_models()
    except Exception as e:
        logger.error("Failed to connect to Ollama: %s", e)
        logger.error("Start Ollama first, or set OLLAMA_HOST to a different address.")
        return

    if not models:
        logger.error("No models found. Pull a model first: ollama pull llama3.2:3b")
        return

    logger.info("Found %d model(s): %s", len(models), [m["name"] for m in models])

    # Connect to server
    conn = NodeConnection(server_url=SERVER_URL, models=models)
    await conn.connect()

    # Run listener and heartbeat concurrently
    await asyncio.gather(
        conn.listen(),
        conn.heartbeat_loop(),
    )


if __name__ == "__main__":
    asyncio.run(main())
