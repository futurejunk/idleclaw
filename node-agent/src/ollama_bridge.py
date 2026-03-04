import asyncio
import logging
import os
import time

from dotenv import load_dotenv
from ollama import AsyncClient

logger = logging.getLogger(__name__)

load_dotenv()

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

_health_cache: dict[str, float | bool] = {"healthy": True, "checked_at": 0.0}
HEALTH_CACHE_TTL = 5  # seconds


async def get_ollama_version() -> str:
    """Get the Ollama server version string."""
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{OLLAMA_HOST}/api/version")
            if resp.status_code == 200:
                return resp.json().get("version", "unknown")
    except Exception:
        pass
    return "unknown"


async def list_models() -> list[dict]:
    client = AsyncClient(host=OLLAMA_HOST)
    response = await client.list()
    return [
        {
            "name": m.model,
            "size": m.size,
        }
        for m in response.models
    ]


async def warmup_models() -> None:
    """Pre-load all models into memory with keep_alive=-1 to prevent unloading."""
    client = AsyncClient(host=OLLAMA_HOST)
    models = await list_models()
    for m in models:
        name = m["name"]
        try:
            await client.chat(
                model=name,
                messages=[{"role": "user", "content": "hi"}],
                keep_alive=-1,
            )
            logger.info("Warmed up model: %s", name)
        except Exception as e:
            logger.warning("Failed to warm up %s: %s", name, e)


async def check_health() -> bool:
    """Check if Ollama is reachable. Caches result for HEALTH_CACHE_TTL seconds."""
    now = time.monotonic()
    if now - _health_cache["checked_at"] < HEALTH_CACHE_TTL:
        return bool(_health_cache["healthy"])
    try:
        client = AsyncClient(host=OLLAMA_HOST)
        await client.list()
        _health_cache["healthy"] = True
    except Exception:
        _health_cache["healthy"] = False
    _health_cache["checked_at"] = now
    return bool(_health_cache["healthy"])


async def stream_chat(params: dict):
    """Stream raw Ollama chunks as plain dicts. Passes params directly to client.chat()."""
    client = AsyncClient(host=OLLAMA_HOST)
    stream = await client.chat(**params)
    async for chunk in stream:
        message = chunk.get("message", {})
        # Convert Ollama Message object to a plain dict, preserving all fields
        msg_dict: dict = {}
        for key in ("role", "content", "thinking", "tool_calls"):
            val = message.get(key) if isinstance(message, dict) else getattr(message, key, None)
            if val is not None and val != "" and val != []:
                # Convert Pydantic objects (e.g. ToolCall) to plain dicts for JSON serialization
                if key == "tool_calls" and isinstance(val, list):
                    val = [tc.model_dump() if hasattr(tc, "model_dump") else tc for tc in val]
                msg_dict[key] = val
        # Preserve any unknown future fields from the message object
        if isinstance(message, dict):
            for key, val in message.items():
                if key not in msg_dict and val is not None and val != "" and val != []:
                    msg_dict[key] = val
        msg_dict.setdefault("role", "assistant")
        msg_dict.setdefault("content", "")
        yield {
            "message": msg_dict,
            "done": chunk.get("done", False),
        }


async def main():
    print(f"Connecting to Ollama at {OLLAMA_HOST}...")
    try:
        models = await list_models()
    except ConnectionError:
        print(f"Error: Ollama is not running at {OLLAMA_HOST}")
        print("Start Ollama first, or set OLLAMA_HOST to a different address.")
        return

    if not models:
        print("No models found. Pull a model first: ollama pull llama3.2:3b")
        return

    print(f"Found {len(models)} model(s):")
    for m in models:
        size_gb = m["size"] / (1024**3)
        print(f"  - {m['name']} ({size_gb:.1f} GB)")

    model = models[0]["name"]
    test_message = "Explain what IdleClaw is in one sentence. Make something up."
    print(f"\nStreaming test with {model}...")
    print(f"Prompt: {test_message}\n")
    print("Response: ", end="", flush=True)

    params = {
        "model": model,
        "messages": [{"role": "user", "content": test_message}],
        "stream": True,
        "keep_alive": -1,
    }
    async for chunk in stream_chat(params):
        thinking = chunk["message"].get("thinking", "")
        content = chunk["message"].get("content", "")
        if thinking:
            print(f"[thinking] {thinking}", end="", flush=True)
        if content:
            print(content, end="", flush=True)

    print("\n\nDone.")


if __name__ == "__main__":
    asyncio.run(main())
