from typing import Any
from pydantic import BaseModel, Field

from app.agents.base import BaseAgent
from app.llm.base import LLMProvider
from app.memory.service import MemoryService
from app.schemas.task import Task


class PlannedTaskItem(BaseModel):
    task_id: str
    title: str
    assigned_role: str
    priority: str = "medium"
    dependencies: list[str] = Field(default_factory=list)


class CoordinatorOutput(BaseModel):
    summary: str
    tasks: list[PlannedTaskItem] = Field(default_factory=list)


class CoordinatorAgent(BaseAgent[CoordinatorOutput]):
    def __init__(self, agent_id: str, llm: LLMProvider, memory_service: MemoryService, prompt: str) -> None:
        super().__init__(
            agent_id=agent_id,
            role="coordinator",
            llm=llm,
            memory_service=memory_service,
            system_prompt=prompt,
            output_schema=CoordinatorOutput,
        )

    async def on_task_completed(
        self,
        project_id: str,
        run_id: str,
        output: CoordinatorOutput,
        task_context: dict[str, Any],
    ) -> None:
        # Create scheduled tasks in the graph
        for t_spec in output.tasks:
            task = Task(
                id=t_spec.task_id,
                run_id=run_id,
                title=t_spec.title,
                assigned_role=t_spec.assigned_role,  # type: ignore
                priority=t_spec.priority,  # type: ignore
                dependencies=t_spec.dependencies,
                status="pending",
            )
            await self.memory_service.repo.create_task(task)
