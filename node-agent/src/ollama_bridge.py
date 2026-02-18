import asyncio
import os

from dotenv import load_dotenv
from ollama import AsyncClient

load_dotenv()

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")


async def list_models() -> list[dict]:
    client = AsyncClient(host=OLLAMA_HOST)
    response = await client.list()
    return [
        {"name": m.model, "size": m.size}
        for m in response.models
    ]


async def stream_chat(model: str, messages: list[dict]):
    client = AsyncClient(host=OLLAMA_HOST)
    stream = await client.chat(model=model, messages=messages, stream=True)
    async for chunk in stream:
        token = chunk["message"]["content"]
        if token:
            yield token


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

    async for token in stream_chat(model, [{"role": "user", "content": test_message}]):
        print(token, end="", flush=True)

    print("\n\nDone.")


if __name__ == "__main__":
    asyncio.run(main())
