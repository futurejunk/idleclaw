from fastapi import APIRouter

router = APIRouter()


@router.get("/api/models")
async def models():
    from server.src.main import registry
    seen: set[str] = set()
    names: list[str] = []
    capabilities: dict[str, dict] = {}
    for node in registry._nodes.values():
        for m in node.models:
            if m.name not in seen:
                seen.add(m.name)
                names.append(m.name)
                capabilities[m.name] = m.capabilities
    return {"models": names, "capabilities": capabilities}
