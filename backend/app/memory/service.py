import uuid
from datetime import datetime
from typing import Any

from app.graph.base import GraphRepository
from app.memory.deduplication import is_duplicate
from app.memory.provenance import ProvenanceRecord
from app.memory.conflicts import ConflictDetector
from app.memory.retrieval import GraphRetrieval
from app.security.redaction import redact_sensitive_data
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
        sanitized_content = redact_sensitive_data(payload.content)
        memory = Memory(
            id=mem_id,
            project_id=project_id,
            run_id=run_id,
            agent_id=payload.agent_id,
            agent_role=payload.agent_role,
            task_id=payload.task_id,
            content=sanitized_content,
            memory_type=payload.memory_type,
            instruction=payload.instruction,
            confidence=payload.confidence,
            tags=payload.tags,
            valid_at=payload.valid_at or datetime.utcnow(),
            invalid_at=payload.invalid_at,
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
        """Correct or update memory. When content is corrected, creates a superseding memory node and penalizes weak rules."""
        existing = await self.repo.get_memory(memory_id)
        if not existing:
            return None

        # Semantic correction creates a superseding memory node
        if updates.content is not None and updates.content != existing.content:
            sanitized_content = redact_sensitive_data(updates.content)
            new_id = f"mem-{uuid.uuid4().hex[:8]}"
            new_mem = Memory(
                id=new_id,
                project_id=existing.project_id,
                run_id=existing.run_id,
                agent_id=existing.agent_id,
                agent_role=existing.agent_role,
                task_id=existing.task_id,
                content=sanitized_content,
                memory_type=updates.memory_type or existing.memory_type,
                instruction=updates.instruction or existing.instruction,
                confidence=updates.confidence if updates.confidence is not None else existing.confidence,
                tags=existing.tags,
                valid_at=datetime.utcnow(),
                invalid_at=None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            saved_new = await self.repo.supersede_memory(memory_id, new_mem)
            # Human correction penalizes procedural rules by -0.15
            await self.penalize_procedural_rules(existing.project_id, delta=0.15)
            return saved_new

        return await self.repo.update_memory(memory_id, updates)

    async def penalize_procedural_rules(self, project_id: str, delta: float = 0.15) -> list[Memory]:
        """Penalize procedural rules when an error, flaw, or contradiction is detected."""
        return await self.repo.adjust_procedural_confidence(project_id, -delta)

    async def boost_procedural_rules(self, project_id: str, delta: float = 0.08) -> list[Memory]:
        """Boost procedural rules when a run is approved or verified."""
        return await self.repo.adjust_procedural_confidence(project_id, delta)

    async def get_procedural_rules(self, project_id: str, min_confidence: float = 0.55, limit: int = 5) -> list[Memory]:
        """Fetch active operational instructions for injection into agent prompts."""
        return await self.repo.get_procedural_memories(project_id, min_confidence=min_confidence, limit=limit)

    async def record_episode(self, run_id: str, memory_id: str, outcome: str) -> None:
        """Record an execution episode (failed, challenged, or completed) linked to graph memory."""
        await self.repo.record_episode(run_id, memory_id, outcome)

    async def get_past_episodes(self, project_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """Retrieve recent execution episodes (past failures / challenges) in the workspace."""
        return await self.repo.get_episodes(project_id, limit=limit)

    async def delete_memory(self, memory_id: str) -> bool:
        return await self.repo.delete_memory(memory_id)

    async def create_claim(
        self,
        project_id: str,
        payload: ClaimCreate,
        run_id: str | None = None,
    ) -> Claim:
        claim_id = f"claim-{uuid.uuid4().hex[:8]}"
        sanitized_text = redact_sensitive_data(payload.text)
        claim = Claim(
            id=claim_id,
            project_id=project_id,
            run_id=run_id,
            agent_id=payload.agent_id,
            agent_role=payload.agent_role,
            text=sanitized_text,
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
