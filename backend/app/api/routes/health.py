from typing import Any
from fastapi import APIRouter
from app.dependencies import GraphRepoDep, SettingsDep

router = APIRouter(tags=["Health"])


@router.get("/health", summary="System Health and Graph Backend Status")
async def health_check(
    repo: GraphRepoDep,
    settings: SettingsDep,
) -> dict[str, Any]:
    db_health = await repo.check_health()
    return {
        "status": "healthy" if db_health.get("status") == "healthy" else "degraded",
        "version": "0.1.0",
        "environment": settings.app_env,
        "graph_backend": settings.graph_backend,
        "database": db_health,
    }
