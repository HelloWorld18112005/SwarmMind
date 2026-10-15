import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any

from app.agents.registry import create_agent
from app.config import Settings, get_settings
from app.graph.base import GraphRepository
from app.graph.factory import get_graph_repository
from app.llm.base import LLMProvider
from app.llm.factory import get_llm_provider
from app.memory.service import MemoryService
from app.orchestration.budgets import BudgetEnforcer
from app.orchestration.event_bus import EventBus, ExecutionEvent, get_event_bus
from app.orchestration.retry_policy import RetryPolicy
from app.orchestration.scheduler import DependencyScheduler
from app.orchestration.state_machine import TaskStateMachine
from app.schemas.run import Run

logger = logging.getLogger(__name__)


class OrchestrationEngine:
    """Multi-agent investigation coordinator executing tasks in dependency order."""

    def __init__(
        self,
        repo: GraphRepository,
        memory_service: MemoryService,
        llm: LLMProvider,
        event_bus: EventBus,
        settings: Settings | None = None,
    ) -> None:
        self.repo = repo
        self.memory_service = memory_service
        self.llm = llm
        self.event_bus = event_bus
        self.settings = settings or get_settings()
        self.scheduler = DependencyScheduler(max_concurrent=self.settings.max_concurrent_agents)
        self.retry_policy = RetryPolicy()
        self._active_runs: dict[str, asyncio.Task[Any]] = {}

    async def execute_investigation(self, run_id: str) -> None:
        """Execute full investigation pipeline for a run."""
        run = await self.repo.get_run(run_id)
        if not run:
            logger.error(f"Run '{run_id}' not found.")
            return

        budget = BudgetEnforcer(self.settings)

        # 1. Start Run
        await self.repo.update_run_status(run_id, "running")
        await self.event_bus.publish(
            ExecutionEvent(
                event_type="run_started",
                run_id=run_id,
                data={"goal": run.goal, "project_id": run.project_id},
            )
        )

        try:
            # 2. Phase A: Coordinator breaks goal into task graph
            logger.info(f"Running Coordinator for Run '{run_id}'...")
            coordinator = create_agent("coordinator", f"coord-{run_id[:6]}", self.llm, self.memory_service)
            budget.record_agent_step("coordinator")

            await self.event_bus.publish(
                ExecutionEvent(
                    event_type="agent_action",
                    run_id=run_id,
                    agent_role="coordinator",
                    data={"action": "Decomposing goal into dependency task graph"},
                )
            )

            coord_output = await coordinator.run(
                project_id=run.project_id,
                run_id=run_id,
                task_context={"goal": run.goal},
            )

            tasks = await self.repo.list_tasks(run_id)
            await self.event_bus.publish(
                ExecutionEvent(
                    event_type="task_plan_created",
                    run_id=run_id,
                    data={"task_count": len(tasks), "summary": coord_output.summary},
                )
            )

            # 3. Phase B: Iterative Dependency Scheduler Loop
            while True:
                budget.check_duration()
                tasks = await self.repo.list_tasks(run_id)
                is_done, final_status = self.scheduler.is_run_finished(tasks)

                if is_done:
                    logger.info(f"All tasks finished for Run '{run_id}'. Final status: {final_status}")
                    break

                ready_tasks = self.scheduler.get_ready_tasks(tasks)
                if not ready_tasks:
                    # Wait for running tasks to finish or check deadlocks
                    await asyncio.sleep(0.3)
                    continue

                for task in ready_tasks:
                    # Execute ready task
                    await self._execute_task(task, run, budget)

            # 4. Finalize Run
            await self.repo.update_run_status(run_id, "completed", completed_at=datetime.utcnow())
            await self.event_bus.publish(
                ExecutionEvent(
                    event_type="run_completed",
                    run_id=run_id,
                    data={"status": "completed", "completed_at": datetime.utcnow().isoformat()},
                )
            )

        except Exception as e:
            logger.error(f"Investigation run '{run_id}' failed: {e}", exc_info=True)
            await self.repo.update_run_status(run_id, "failed")
            await self.event_bus.publish(
                ExecutionEvent(
                    event_type="run_failed",
                    run_id=run_id,
                    data={"error": str(e)},
                )
            )

    async def _execute_task(self, task: Any, run: Run, budget: BudgetEnforcer) -> None:
        """Execute a single assigned agent task."""
        task_id = task.id
        role = task.assigned_role

        # Update status -> running
        await self.repo.update_task_status(task_id, "running")
        await self.event_bus.publish(
            ExecutionEvent(
                event_type="task_started",
                run_id=run.id,
                task_id=task_id,
                agent_role=role,
                data={"title": task.title},
            )
        )

        try:
            budget.record_agent_step(role)
            agent_id = f"{role[:4]}-{uuid.uuid4().hex[:6]}"
            agent = create_agent(role, agent_id, self.llm, self.memory_service)

            # Gather prerequisite task results
            prereq_results = {}
            for dep_id in task.dependencies:
                dep_t = await self.repo.get_task(dep_id)
                if dep_t and dep_t.result:
                    prereq_results[dep_t.title] = dep_t.result

            task_context = {
                "goal": run.goal,
                "task_title": task.title,
                "task_description": task.description,
                "prerequisites": prereq_results,
            }

            output = await self.retry_policy.execute_with_retry(
                lambda: agent.run(run.project_id, run.id, task_context),
                operation_name=f"task_{task_id}_{role}",
            )

            result_dict = output.model_dump()
            await self.repo.update_task_status(task_id, "completed", result=result_dict)
            await self.event_bus.publish(
                ExecutionEvent(
                    event_type="task_completed",
                    run_id=run.id,
                    task_id=task_id,
                    agent_role=role,
                    data={"summary": result_dict.get("summary", "Task completed")},
                )
            )

        except Exception as err:
            logger.error(f"Task '{task_id}' failed: {err}")
            await self.repo.update_task_status(task_id, "failed", error=str(err))
            await self.event_bus.publish(
                ExecutionEvent(
                    event_type="task_failed",
                    run_id=run.id,
                    task_id=task_id,
                    agent_role=role,
                    data={"error": str(err)},
                )
            )

    def start_background_run(self, run_id: str) -> None:
        """Launch investigation in an asynchronous background task."""
        task = asyncio.create_task(self.execute_investigation(run_id))
        self._active_runs[run_id] = task

    async def cancel_run(self, run_id: str) -> bool:
        """Cancel active investigation run."""
        if run_id in self._active_runs:
            self._active_runs[run_id].cancel()
            del self._active_runs[run_id]

        await self.repo.update_run_status(run_id, "cancelled")
        await self.event_bus.publish(
            ExecutionEvent(
                event_type="run_cancelled",
                run_id=run_id,
                data={"message": "Run cancelled by user request"},
            )
        )
        return True


_engine_instance: OrchestrationEngine | None = None


async def get_orchestration_engine() -> OrchestrationEngine:
    global _engine_instance
    if _engine_instance is None:
        repo = await get_graph_repository()
        memory_service = MemoryService(repo)
        llm = get_llm_provider()
        event_bus = get_event_bus()
        _engine_instance = OrchestrationEngine(repo, memory_service, llm, event_bus)
    return _engine_instance
