from typing import Any
from pydantic import BaseModel, Field

from app.agents.base import BaseAgent
from app.llm.base import LLMProvider
from app.memory.service import MemoryService
from app.schemas.memory import MemoryCreate


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
