import time
from collections import Counter

from fastapi import APIRouter

router = APIRouter()


@router.get("/metrics")
async def metrics():
    from server.src.main import registry, stats
    from server.src.routers.health import _start_time

    # Count nodes per model
    model_counts: Counter[str] = Counter()
    for node in registry.all_nodes():
        for m in node.models:
            model_counts[m.name] += 1

    models_available = [
        {"name": name, "node_count": count}
        for name, count in model_counts.most_common()
    ]

    return {
        "nodes_connected": registry.node_count,
        "nodes_registered_total": stats.nodes_registered_total,
        "requests_total": stats.requests_total,
        "requests_active": stats.requests_active,
        "requests_errors_total": stats.requests_errors_total,
        "models_available": models_available,
        "uptime_seconds": round(time.time() - _start_time),
    }
