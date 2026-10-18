from typing import Any
from fastapi import APIRouter, HTTPException, status
from app.dependencies import GraphRepoDep, SettingsDep

router = APIRouter(tags=["Health"])


@router.get("/health", summary="System Health and Graph Backend Status")
async def health_check(
    repo: GraphRepoDep,
    settings: SettingsDep,
) -> dict[str, Any]:
    db_health = await repo.check_health()
    is_healthy = db_health.get("status") == "healthy"

    if settings.graph_backend == "falkordb" and not is_healthy:
        error_msg = db_health.get("error", "FalkorDB cluster unreachable")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"FalkorDB connection failed: {error_msg}. Verify host/port or start Docker container.",
        )

    db_name = db_health.get("database", settings.graph_backend)
    node_count = db_health.get("nodes", 0)
    edge_count = db_health.get("edges", 0)

    return {
        "status": "healthy" if is_healthy else "degraded",
        "database": db_name,
        "nodes": node_count,
        "edges": edge_count,
        "version": "0.1.0",
        "environment": settings.app_env,
        "graph_backend": settings.graph_backend,
        "details": db_health,
    }
