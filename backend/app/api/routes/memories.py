from fastapi import APIRouter, HTTPException, Query, status
from app.dependencies import GraphRepoDep
from app.memory.service import MemoryService
from app.schemas.memory import Memory, MemoryCreate, MemoryUpdate

router = APIRouter(tags=["Memories"])


@router.post("/projects/{project_id}/memories", response_model=Memory, status_code=status.HTTP_201_CREATED, summary="Store a memory with provenance")
async def create_memory(project_id: str, payload: MemoryCreate, repo: GraphRepoDep) -> Memory:
    service = MemoryService(repo)
    memory, _ = await service.save_memory(project_id=project_id, payload=payload)
    return memory


@router.get("/projects/{project_id}/memories", response_model=list[Memory], summary="Search and list project graph memories")
async def list_memories(
    project_id: str,
    repo: GraphRepoDep,
    query: str | None = Query(default=None, description="Optional text filter"),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[Memory]:
    service = MemoryService(repo)
    return await service.list_memories(project_id=project_id, query=query, limit=limit)


@router.get("/memories/{memory_id}", response_model=Memory, summary="Get memory details")
async def get_memory(memory_id: str, repo: GraphRepoDep) -> Memory:
    service = MemoryService(repo)
    mem = await service.get_memory(memory_id)
    if not mem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Memory '{memory_id}' not found")
    return mem


@router.patch("/memories/{memory_id}", response_model=Memory, summary="Correct or update a memory")
async def update_memory(memory_id: str, payload: MemoryUpdate, repo: GraphRepoDep) -> Memory:
    service = MemoryService(repo)
    updated = await service.update_memory(memory_id, payload)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Memory '{memory_id}' not found")
    return updated


@router.delete("/memories/{memory_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a memory")
async def delete_memory(memory_id: str, repo: GraphRepoDep) -> None:
    service = MemoryService(repo)
    deleted = await service.delete_memory(memory_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Memory '{memory_id}' not found")
