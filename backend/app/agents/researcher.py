from typing import Any
from pydantic import BaseModel, Field

from app.agents.base import BaseAgent
from app.agents.tools.evidence import EvidenceTool
from app.llm.base import LLMProvider
from app.memory.service import MemoryService


class ResearchFinding(BaseModel):
    claim_text: str
    confidence: float = 0.8
    source_title: str
    source_uri: str = ""
    source_type: str = "document"


class ResearcherOutput(BaseModel):
    summary: str
    findings: list[ResearchFinding] = Field(default_factory=list)


class ResearcherAgent(BaseAgent[ResearcherOutput]):
    def __init__(self, agent_id: str, llm: LLMProvider, memory_service: MemoryService, prompt: str) -> None:
        super().__init__(
            agent_id=agent_id,
            role="researcher",
            llm=llm,
            memory_service=memory_service,
            system_prompt=prompt,
            output_schema=ResearcherOutput,
        )
        self.evidence_tool = EvidenceTool(memory_service)

    async def on_task_completed(
        self,
        project_id: str,
        run_id: str,
        output: ResearcherOutput,
        task_context: dict[str, Any],
    ) -> None:
        # Save each claim with source into the graph
        for finding in output.findings:
            await self.evidence_tool.record_claim(
                project_id=project_id,
                text=finding.claim_text,
                confidence=finding.confidence,
                agent_id=self.agent_id,
                agent_role=self.role,
                run_id=run_id,
                source_title=finding.source_title,
                source_uri=finding.source_uri,
                source_type=finding.source_type,
            )
