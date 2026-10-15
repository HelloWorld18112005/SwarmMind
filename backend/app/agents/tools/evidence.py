from app.memory.service import MemoryService
from app.schemas.claim import Claim, ClaimCreate, Source


class EvidenceTool:
    """Tool enabling agents to record attributed claims and link contradictions."""

    def __init__(self, memory_service: MemoryService) -> None:
        self.service = memory_service

    async def record_claim(
        self,
        project_id: str,
        text: str,
        confidence: float,
        agent_id: str,
        agent_role: str,
        run_id: str | None = None,
        source_title: str = "",
        source_uri: str = "",
        source_type: str = "document",
    ) -> Claim:
        source_id = None
        if source_title:
            import uuid
            source_id = f"src-{uuid.uuid4().hex[:6]}"
            src = Source(id=source_id, title=source_title, uri=source_uri, source_type=source_type)
            await self.service.repo.save_source(src)

        payload = ClaimCreate(
            text=text,
            confidence=confidence,
            agent_id=agent_id,
            agent_role=agent_role,
            source_ids=[source_id] if source_id else [],
        )
        return await self.service.create_claim(project_id=project_id, payload=payload, run_id=run_id)

    async def record_contradiction(
        self,
        claim_a_id: str,
        claim_b_id: str,
        reason: str = "",
    ) -> None:
        await self.service.record_contradiction(claim_a_id, claim_b_id, notes=reason)
