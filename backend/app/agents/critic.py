from typing import Any
from pydantic import BaseModel, Field

from app.agents.base import BaseAgent
from app.llm.base import LLMProvider
from app.memory.service import MemoryService
from app.schemas.claim import ClaimCreate


class ContradictionItem(BaseModel):
    claim_a: str
    claim_b: str
    dispute_reason: str
    recommendation: str = ""


class CriticOutput(BaseModel):
    summary: str
    verified_claims: list[str] = Field(default_factory=list)
    contradictions: list[ContradictionItem] = Field(default_factory=list)


class CriticAgent(BaseAgent[CriticOutput]):
    def __init__(self, agent_id: str, llm: LLMProvider, memory_service: MemoryService, prompt: str) -> None:
        super().__init__(
            agent_id=agent_id,
            role="critic",
            llm=llm,
            memory_service=memory_service,
            system_prompt=prompt,
            output_schema=CriticOutput,
        )

    async def on_task_completed(
        self,
        project_id: str,
        run_id: str,
        output: CriticOutput,
        task_context: dict[str, Any],
    ) -> None:
        # Record detected contradictions into graph
        for c in output.contradictions:
            # Save temporary claim representations if needed, or find existing
            claim_a = await self.memory_service.create_claim(
                project_id=project_id,
                payload=ClaimCreate(text=c.claim_a, confidence=0.85, agent_id=self.agent_id, agent_role=self.role),
                run_id=run_id,
            )
            claim_b = await self.memory_service.create_claim(
                project_id=project_id,
                payload=ClaimCreate(text=c.claim_b, confidence=0.82, agent_id=self.agent_id, agent_role=self.role),
                run_id=run_id,
            )
            await self.memory_service.record_contradiction(
                claim_a_id=claim_a.id,
                claim_b_id=claim_b.id,
                notes=f"{c.dispute_reason} | Recommendation: {c.recommendation}",
            )
