from typing import Literal

from pydantic import BaseModel, Field

from server.src.config import settings


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=settings.max_message_length)


class ChatRequest(BaseModel):
    model: str = Field(min_length=1, max_length=settings.max_model_name_length)
    messages: list[ChatMessage] = Field(min_length=1, max_length=settings.max_messages_per_request)
    think: bool = False
