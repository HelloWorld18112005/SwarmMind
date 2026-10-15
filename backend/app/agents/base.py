import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Generic, Type, TypeVar
from pydantic import BaseModel, ValidationError

from app.llm.base import ChatMessage, LLMProvider
from app.memory.service import MemoryService

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)


class BaseAgent(ABC, Generic[T]):
    """Abstract base class for all SwarmMind specialized agents."""

    def __init__(
        self,
        agent_id: str,
        role: str,
        llm: LLMProvider,
        memory_service: MemoryService,
        system_prompt: str,
        output_schema: Type[T],
    ) -> None:
        self.agent_id = agent_id
        self.role = role
        self.llm = llm
        self.memory_service = memory_service
        self.system_prompt = system_prompt
        self.output_schema = output_schema
        self.step_count = 0

    async def run(
        self,
        project_id: str,
        run_id: str,
        task_context: dict[str, Any],
    ) -> T:
        """Execute the agent task and return validated structured output."""
        self.step_count += 1
        messages = [
            ChatMessage(role="system", content=self.system_prompt),
            ChatMessage(
                role="user",
                content=f"Project ID: {project_id}\nRun ID: {run_id}\nTask Context:\n{json.dumps(task_context, indent=2)}",
            ),
        ]

        logger.info(f"Agent [{self.role}:{self.agent_id}] generating output...")
        llm_resp = await self.llm.generate(messages, response_json=True)

        try:
            parsed_json = json.loads(llm_resp.content)
            validated = self.output_schema.model_validate(parsed_json)
        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(f"Agent [{self.role}] output validation failed: {e}\nContent: {llm_resp.content}")
            raise ValueError(f"Agent [{self.role}] returned invalid structured output: {e}") from e

        # Post-execution hook for graph side-effects
        await self.on_task_completed(project_id, run_id, validated, task_context)
        return validated

    @abstractmethod
    async def on_task_completed(
        self,
        project_id: str,
        run_id: str,
        output: T,
        task_context: dict[str, Any],
    ) -> None:
        """Hook for saving findings, claims, or relationships to the graph."""
        ...
