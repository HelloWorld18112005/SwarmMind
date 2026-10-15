import asyncio
from functools import wraps
import pytest
from app.graph.local_adapter import LocalGraphAdapter
from app.llm.providers.mock_provider import MockProvider
from app.memory.service import MemoryService
from app.orchestration.budgets import BudgetEnforcer
from app.orchestration.engine import OrchestrationEngine
from app.orchestration.event_bus import EventBus, ExecutionEvent
from app.orchestration.scheduler import DependencyScheduler
from app.orchestration.state_machine import TaskStateMachine
from app.schemas.project import Project
from app.schemas.run import Run
from app.schemas.task import Task


def async_test(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper


def test_task_state_machine():
    assert TaskStateMachine.can_transition("pending", "ready") is True
    assert TaskStateMachine.can_transition("ready", "running") is True
    assert TaskStateMachine.can_transition("running", "completed") is True
    assert TaskStateMachine.can_transition("completed", "running") is False


def test_dependency_scheduler():
    scheduler = DependencyScheduler(max_concurrent=2)
    t1 = Task(id="t1", run_id="r1", title="Task 1", assigned_role="researcher", status="completed")
    t2 = Task(id="t2", run_id="r1", title="Task 2", assigned_role="analyst", status="pending", dependencies=["t1"])
    t3 = Task(id="t3", run_id="r1", title="Task 3", assigned_role="critic", status="pending", dependencies=["t2"])

    ready = scheduler.get_ready_tasks([t1, t2, t3])
    assert len(ready) == 1
    assert ready[0].id == "t2"  # Only t2 is ready because t1 is completed


def test_budget_enforcer():
    enforcer = BudgetEnforcer()
    enforcer.max_agent_steps = 2
    enforcer.record_agent_step("researcher")
    enforcer.record_agent_step("researcher")
    with pytest.raises(RuntimeError):
        enforcer.record_agent_step("researcher")


@async_test
async def test_full_investigation_orchestration():
    repo = LocalGraphAdapter()
    await repo.initialize()
    memory_service = MemoryService(repo)
    llm = MockProvider()
    event_bus = EventBus()

    engine = OrchestrationEngine(repo, memory_service, llm, event_bus)

    # Setup project and run
    await repo.create_project(Project(id="p-orch", name="Orchestration Project"))
    await repo.create_run(Run(id="r-orch", project_id="p-orch", goal="Full swarm evaluation"))

    # Execute investigation end-to-end
    await engine.execute_investigation("r-orch")

    # Verify run completed
    run = await repo.get_run("r-orch")
    assert run is not None
    assert run.status == "completed"

    # Verify tasks were created and executed
    tasks = await repo.list_tasks("r-orch")
    assert len(tasks) >= 3
    assert all(t.status == "completed" for t in tasks)

    # Verify findings were stored in the graph
    claims = await repo.list_claims("p-orch", "r-orch")
    assert len(claims) >= 1

    await repo.close()
