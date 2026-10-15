from typing import Any
from pydantic import BaseModel, Field

from app.agents.base import BaseAgent
from app.llm.base import LLMProvider
from app.memory.service import MemoryService
from app.schemas.memory import MemoryCreate


class RecommendationPlan(BaseModel):
    title: str
    description: str
    priority: str = "high"
    risks: list[str] = Field(default_factory=list)


class PlannerOutput(BaseModel):
    summary: str
    recommendations: list[RecommendationPlan] = Field(default_factory=list)


class PlannerAgent(BaseAgent[PlannerOutput]):
    def __init__(self, agent_id: str, llm: LLMProvider, memory_service: MemoryService, prompt: str) -> None:
        super().__init__(
            agent_id=agent_id,
            role="planner",
            llm=llm,
            memory_service=memory_service,
            system_prompt=prompt,
            output_schema=PlannerOutput,
        )

    async def on_task_completed(
        self,
        project_id: str,
        run_id: str,
        output: PlannerOutput,
        task_context: dict[str, Any],
    ) -> None:
        # Save recommendations as actionable rules in graph memory
        for plan in output.recommendations:
            await self.memory_service.save_memory(
                project_id=project_id,
                payload=MemoryCreate(
                    content=f"Recommendation: {plan.title} - {plan.description}",
                    memory_type="rule",
                    agent_id=self.agent_id,
                    agent_role=self.role,
                    confidence=0.90,
                    tags=["recommendation", plan.priority],
                ),
                run_id=run_id,
            )
