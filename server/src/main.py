import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.src.config import settings
from server.src.routers import chat, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    health.set_start_time(time.time())
    yield


app = FastAPI(title="IdleClaw", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(chat.router)
