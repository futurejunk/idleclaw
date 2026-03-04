from fastapi import APIRouter

router = APIRouter()


@router.get("/api/models")
async def models():
    from server.src.main import registry
    seen: dict[str, int] = {}  # name -> size
    capabilities: dict[str, dict] = {}
    for node in registry._nodes.values():
        for m in node.models:
            if m.name not in seen:
                seen[m.name] = m.size
                capabilities[m.name] = m.capabilities
    # Sort by size descending so the best model is first (used as default in UI)
    names = sorted(seen, key=lambda n: seen[n], reverse=True)
    return {"models": names, "capabilities": capabilities}
