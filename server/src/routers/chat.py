import asyncio
import json
import uuid

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from server.src.models.chat import ChatRequest

router = APIRouter()

MOCK_RESPONSE = (
    "I'm a mock response from IdleClaw. In a future version, this message "
    "will come from a real Ollama model running on a community node. "
    "For now, this proves the streaming pipeline works end-to-end."
)


async def _mock_stream(request: ChatRequest):
    chat_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
    words = MOCK_RESPONSE.split(" ")

    for i, word in enumerate(words):
        token = word if i == 0 else f" {word}"
        chunk = {
            "id": chat_id,
            "object": "chat.completion.chunk",
            "model": request.model,
            "choices": [{"delta": {"content": token}, "index": 0}],
        }
        yield json.dumps(chunk)
        await asyncio.sleep(0.05)

    yield "[DONE]"


@router.post("/api/chat")
async def chat(request: ChatRequest):
    async def event_generator():
        async for data in _mock_stream(request):
            yield {"data": data}

    return EventSourceResponse(event_generator())
