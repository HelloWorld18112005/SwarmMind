import uuid
from datetime import datetime
from typing import Any

from app.graph.base import GraphRepository
from app.memory.deduplication import is_duplicate
from app.memory.provenance import ProvenanceRecord
from app.memory.conflicts import ConflictDetector
from app.memory.retrieval import GraphRetrieval
from app.schemas.memory import Memory, MemoryCreate, MemoryUpdate
from app.schemas.claim import Claim, ClaimCreate, Source
from app.schemas.graph import GraphData


class MemoryService:
    """High-level orchestrator for shared graph memory operations."""

    def __init__(self, repo: GraphRepository) -> None:
        self.repo = repo
        self.conflicts = ConflictDetector(repo)
        self.retrieval = GraphRetrieval(repo)

    async def save_memory(
        self,
        project_id: str,
        payload: MemoryCreate,
        run_id: str | None = None,
        check_duplicates: bool = True,
    ) -> tuple[Memory, bool]:
        """Store a memory in the graph, with optional deduplication.

        Returns (memory, is_new).
        """
        if check_duplicates:
            existing = await self.repo.list_memories(project_id=project_id, limit=100)
            existing_texts = [m.content for m in existing]
            is_dup, match, sim = is_duplicate(payload.content, existing_texts)
            if is_dup and match:
                for m in existing:
                    if m.content == match:
                        return m, False

        mem_id = f"mem-{uuid.uuid4().hex[:8]}"
        memory = Memory(
            id=mem_id,
            project_id=project_id,
            run_id=run_id,
            agent_id=payload.agent_id,
            agent_role=payload.agent_role,
            task_id=payload.task_id,
            content=payload.content,
            memory_type=payload.memory_type,
            confidence=payload.confidence,
            tags=payload.tags,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        saved = await self.repo.save_memory(memory)
        return saved, True

    async def list_memories(
        self,
        project_id: str,
        query: str | None = None,
        limit: int = 50,
    ) -> list[Memory]:
        return await self.repo.list_memories(project_id=project_id, query=query, limit=limit)

    async def get_memory(self, memory_id: str) -> Memory | None:
        return await self.repo.get_memory(memory_id)

    async def update_memory(self, memory_id: str, updates: MemoryUpdate) -> Memory | None:
        return await self.repo.update_memory(memory_id, updates)

    async def delete_memory(self, memory_id: str) -> bool:
        return await self.repo.delete_memory(memory_id)

    async def create_claim(
        self,
        project_id: str,
        payload: ClaimCreate,
        run_id: str | None = None,
    ) -> Claim:
        claim_id = f"claim-{uuid.uuid4().hex[:8]}"
        claim = Claim(
            id=claim_id,
            project_id=project_id,
            run_id=run_id,
            agent_id=payload.agent_id,
            agent_role=payload.agent_role,
            text=payload.text,
            confidence=payload.confidence,
            status="proposed",
            supporting_source_ids=payload.source_ids,
            created_at=datetime.utcnow(),
        )
        saved = await self.repo.save_claim(claim)
        return saved

    async def record_contradiction(
        self,
        claim_a_id: str,
        claim_b_id: str,
        notes: str = "",
    ) -> None:
        await self.conflicts.register_contradiction(claim_a_id, claim_b_id, notes)

    async def get_project_graph(
        self,
        project_id: str,
        node_types: list[str] | None = None,
        limit: int = 150,
    ) -> GraphData:
        return await self.retrieval.get_subgraph(project_id, node_types=node_types, limit=limit)

    async def traverse_path(
        self,
        project_id: str,
        node_id: str,
        depth: int = 2,
    ) -> GraphData:
        return await self.retrieval.trace_provenance(project_id, node_id, depth)

    async def get_conflicts(self, project_id: str) -> list[dict[str, Any]]:
        return await self.conflicts.get_project_conflicts(project_id)
