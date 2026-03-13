import time

from fastapi import APIRouter, HTTPException, Request

from server.src.config import settings

router = APIRouter()


def _mask_ip(ip: str) -> str:
    """Mask IP to show only first two octets: 192.168.1.50 -> 192.168.x.x"""
    parts = ip.split(".")
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.x.x"
    return ip  # non-IPv4, return as-is


def _check_admin_token(request: Request) -> None:
    if not settings.admin_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    auth = request.headers.get("authorization", "")
    if auth != f"Bearer {settings.admin_token}":
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.get("/admin/nodes")
async def admin_nodes(request: Request):
    from server.src.main import registry

    _check_admin_token(request)

    now = time.time()
    nodes = []
    for node in registry.all_nodes():
        nodes.append({
            "node_id": node.node_id,
            "ip": _mask_ip(node.ip),
            "models": [m.name for m in node.models],
            "connected_seconds": round(now - node.connected_at),
            "active_requests": node.active_requests,
            "ollama_version": node.ollama_version,
        })

    return {"nodes": nodes}
