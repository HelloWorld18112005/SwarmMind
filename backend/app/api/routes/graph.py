from typing import Any
from fastapi import APIRouter, Query, HTTPException
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


@router.get("/paths", response_model=GraphData, summary="Multi-hop traversal or explainable shortest path between nodes")
async def traverse_path(
    project_id: str,
    repo: GraphRepoDep,
    node_id: str | None = Query(default=None, description="Starting node ID for multi-hop traversal"),
    start_id: str | None = Query(default=None, description="Start node ID for shortest path tracing"),
    end_id: str | None = Query(default=None, description="Target node ID for shortest path tracing"),
    depth: int = Query(default=2, ge=1, le=4),
) -> GraphData:
    service = MemoryService(repo)
    if start_id and end_id:
        path_names = await repo.trace_evidence_path(project_id, start_id, end_id)
        graph_data = await repo.find_shortest_path(project_id, start_id, end_id)
        graph_data.explainable_path = path_names
        return graph_data

    target_node = node_id or start_id
    if target_node:
        return await service.traverse_path(project_id, node_id=target_node, depth=depth)

    raise HTTPException(status_code=400, detail="Must provide 'node_id' or both 'start_id' and 'end_id'")


@router.get("/shortest-path", response_model=GraphData, summary="Find shortest graph path between any two nodes")
async def get_shortest_path(
    project_id: str,
    repo: GraphRepoDep,
    start_id: str = Query(..., description="Start node ID"),
    end_id: str = Query(..., description="Target node ID"),
) -> GraphData:
    path_names = await repo.trace_evidence_path(project_id, start_id, end_id)
    graph_data = await repo.find_shortest_path(project_id, start_id, end_id)
    graph_data.explainable_path = path_names
    return graph_data


@router.get("/conflicts", summary="Retrieve all detected contradictions in the project graph")
async def get_conflicts(
    project_id: str,
    repo: GraphRepoDep,
) -> list[dict[str, Any]]:
    return await repo.get_disputes_with_evidence(project_id)
