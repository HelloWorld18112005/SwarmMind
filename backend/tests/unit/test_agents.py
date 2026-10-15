import asyncio
from functools import wraps
import pytest
from app.agents.registry import create_agent
from app.graph.local_adapter import LocalGraphAdapter
from app.llm.providers.mock_provider import MockProvider
from app.memory.service import MemoryService
from app.schemas.project import Project
from app.schemas.run import Run


def async_test(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper


@pytest.fixture
def env():
    repo = LocalGraphAdapter()
    asyncio.run(repo.initialize())
    service = MemoryService(repo)
    llm = MockProvider()
    yield repo, service, llm
    asyncio.run(repo.close())


@async_test
async def test_coordinator_agent_execution(env):
    repo, service, llm = env
    await repo.create_project(Project(id="p-agent-test", name="Agent Test Project"))
    await repo.create_run(Run(id="r-test", project_id="p-agent-test", goal="Test multi-agent collaboration"))

    coordinator = create_agent("coordinator", "agent-coord-1", llm, service)
    output = await coordinator.run(
        project_id="p-agent-test",
        run_id="r-test",
        task_context={"goal": "Evaluate AI tutoring"},
    )

    assert len(output.tasks) >= 3
    tasks_in_graph = await repo.list_tasks("r-test")
    assert len(tasks_in_graph) >= 3


@async_test
async def test_researcher_agent_execution(env):
    repo, service, llm = env
    await repo.create_project(Project(id="p-research", name="Research Project"))
    await repo.create_run(Run(id="r-res", project_id="p-research", goal="Market research"))

    researcher = create_agent("researcher", "agent-res-1", llm, service)
    output = await researcher.run(
        project_id="p-research",
        run_id="r-res",
        task_context={"topic": "EdTech TAM"},
    )

    assert len(output.findings) >= 1
    claims_in_graph = await repo.list_claims("p-research", "r-res")
    assert len(claims_in_graph) >= 1


@async_test
async def test_critic_contradiction_detection(env):
    repo, service, llm = env
    await repo.create_project(Project(id="p-critic", name="Critic Project"))
    await repo.create_run(Run(id="r-critic", project_id="p-critic", goal="Check evidence conflicts"))

    critic = create_agent("critic", "agent-critic-1", llm, service)
    output = await critic.run(
        project_id="p-critic",
        run_id="r-critic",
        task_context={"check": "market estimates"},
    )

    assert len(output.contradictions) >= 1
    conflicts = await service.get_conflicts("p-critic")
    assert len(conflicts) >= 1
