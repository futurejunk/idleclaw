import time

from fastapi import APIRouter

router = APIRouter()

_start_time: float = 0.0


def set_start_time(t: float) -> None:
    global _start_time
    _start_time = t


@router.get("/health")
async def health():
    return {
        "status": "healthy",
        "uptime_seconds": round(time.time() - _start_time),
    }
