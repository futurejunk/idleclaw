from fastapi import APIRouter

router = APIRouter()


@router.get("/api/models")
async def models():
    from server.src.main import registry
    seen: set[str] = set()
    result: list[str] = []
    for node in registry._nodes.values():
        for m in node.models:
            if m.name not in seen:
                seen.add(m.name)
                result.append(m.name)
    return {"models": result}
