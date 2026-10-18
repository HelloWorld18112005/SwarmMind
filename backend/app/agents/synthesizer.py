import logging
from typing import Any
from pydantic import BaseModel, Field

from app.agents.base import BaseAgent
from app.llm.base import LLMProvider
from app.memory.service import MemoryService
from app.schemas.memory import MemoryCreate

logger = logging.getLogger(__name__)


class SynthesizerOutput(BaseModel):
    title: str
    executive_summary: str
    key_findings: list[str] = Field(default_factory=list)
    unresolved_disputes: list[str] = Field(default_factory=list)
    confidence_assessment: str = ""


class SynthesizerAgent(BaseAgent[SynthesizerOutput]):
    def __init__(self, agent_id: str, llm: LLMProvider, memory_service: MemoryService, prompt: str) -> None:
        super().__init__(
            agent_id=agent_id,
            role="synthesizer",
            llm=llm,
            memory_service=memory_service,
            system_prompt=prompt,
            output_schema=SynthesizerOutput,
        )

    async def run(
        self,
        project_id: str,
        run_id: str,
        task_context: dict[str, Any],
    ) -> SynthesizerOutput:
        # Query native PageRank centrality to weight anchoring findings for the executive summary
        try:
            authority = await self.memory_service.repo.get_claim_authority(project_id, limit=5)
            if authority:
                task_context["anchoring_findings_pagerank"] = [
                    f"Claim: '{a.get('text') or a.get('claim')}' (PageRank Score: {a.get('score', 0):.4f})"
                    for a in authority
                ]
        except Exception as e:
            logger.debug(f"Synthesizer authority ranking note: {e}")

        return await super().run(project_id, run_id, task_context)

    async def on_task_completed(
        self,
        project_id: str,
        run_id: str,
        output: SynthesizerOutput,
        task_context: dict[str, Any],
    ) -> None:
        # Save final report summary into shared graph memory
        await self.memory_service.save_memory(
            project_id=project_id,
            payload=MemoryCreate(
                content=f"Final Synthesis: {output.title}\n{output.executive_summary}",
                memory_type="summary",
                agent_id=self.agent_id,
                agent_role=self.role,
                confidence=0.92,
                tags=["report", "synthesis"],
            ),
            run_id=run_id,
        )
