from typing import Any
from fastapi import APIRouter, Query
from app.dependencies import GraphRepoDep
from app.memory.service import MemoryService
from app.schemas.graph import GraphData

router = APIRouter(prefix="/projects/{project_id}/graph", tags=["Knowledge Graph"])


@router.get("", response_model=GraphData, summary="Retrieve filtered project graph")
async def get_project_graph(
    project_id: str,
    repo: GraphRepoDep,
    node_types: str | None = Query(default=None, description="Comma-separated node types filter, e.g. 'Claim,Memory,Task'"),
    limit: int = Query(default=150, ge=1, le=500),
) -> GraphData:
    service = MemoryService(repo)
    types_list = [t.strip() for t in node_types.split(",")] if node_types else None
    return await service.get_project_graph(project_id, node_types=types_list, limit=limit)


@router.get("/paths", response_model=GraphData, summary="Multi-hop traversal from a specific node")
async def traverse_path(
    project_id: str,
    repo: GraphRepoDep,
    node_id: str = Query(..., description="Starting node ID"),
    depth: int = Query(default=2, ge=1, le=4),
) -> GraphData:
    service = MemoryService(repo)
    return await service.traverse_path(project_id, node_id=node_id, depth=depth)


@router.get("/conflicts", summary="Retrieve all detected contradictions in the project graph")
async def get_conflicts(
    project_id: str,
    repo: GraphRepoDep,
) -> list[dict[str, Any]]:
    service = MemoryService(repo)
    return await service.get_conflicts(project_id)
