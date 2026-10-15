from typing import Any
from pydantic import BaseModel, Field

from app.agents.base import BaseAgent
from app.llm.base import LLMProvider
from app.memory.service import MemoryService
from app.schemas.memory import MemoryCreate


class AnalyticalInference(BaseModel):
    text: str
    confidence: float = 0.85
    memory_type: str = "fact"
    tags: list[str] = Field(default_factory=list)


class AnalystOutput(BaseModel):
    summary: str
    inferences: list[AnalyticalInference] = Field(default_factory=list)


class AnalystAgent(BaseAgent[AnalystOutput]):
    def __init__(self, agent_id: str, llm: LLMProvider, memory_service: MemoryService, prompt: str) -> None:
        super().__init__(
            agent_id=agent_id,
            role="analyst",
            llm=llm,
            memory_service=memory_service,
            system_prompt=prompt,
            output_schema=AnalystOutput,
        )

    async def on_task_completed(
        self,
        project_id: str,
        run_id: str,
        output: AnalystOutput,
        task_context: dict[str, Any],
    ) -> None:
        # Persist analytical inferences to shared graph memory
        for inf in output.inferences:
            await self.memory_service.save_memory(
                project_id=project_id,
                payload=MemoryCreate(
                    content=inf.text,
                    memory_type=inf.memory_type,  # type: ignore
                    agent_id=self.agent_id,
                    agent_role=self.role,
                    confidence=inf.confidence,
                    tags=inf.tags,
                ),
                run_id=run_id,
            )
