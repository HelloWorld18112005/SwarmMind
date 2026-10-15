import asyncio
from functools import wraps
import pytest
from app.graph.local_adapter import LocalGraphAdapter
from app.schemas.project import Project, ProjectUpdate
from app.schemas.run import Run
from app.schemas.task import Task
from app.schemas.claim import Claim


def async_test(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper


@pytest.fixture
def repo():
    adapter = LocalGraphAdapter()
    asyncio.run(adapter.initialize())
    yield adapter
    asyncio.run(adapter.close())


@async_test
async def test_project_lifecycle(repo: LocalGraphAdapter):
    p = Project(id="proj-1", name="AI Tutoring Strategy", description="Market analysis")
    created = await repo.create_project(p)
    assert created.id == "proj-1"
    assert created.name == "AI Tutoring Strategy"

    fetched = await repo.get_project("proj-1")
    assert fetched is not None
    assert fetched.name == "AI Tutoring Strategy"

    all_projects = await repo.list_projects()
    assert len(all_projects) == 1

    updated = await repo.update_project("proj-1", ProjectUpdate(name="AI Tutoring Product Plan"))
    assert updated is not None
    assert updated.name == "AI Tutoring Product Plan"

    deleted = await repo.delete_project("proj-1")
    assert deleted is True
    assert await repo.get_project("proj-1") is None


@async_test
async def test_run_and_task_graph(repo: LocalGraphAdapter):
    await repo.create_project(Project(id="p1", name="Project 1"))

    run = Run(id="run-1", project_id="p1", goal="Evaluate AI tutoring feasibility")
    await repo.create_run(run)

    t1 = Task(id="t1", run_id="run-1", title="Market Research", assigned_role="researcher")
    t2 = Task(id="t2", run_id="run-1", title="Synthesize Market", assigned_role="synthesizer", dependencies=["t1"])
    await repo.create_task(t1)
    await repo.create_task(t2)

    tasks = await repo.list_tasks("run-1")
    assert len(tasks) == 2

    graph = await repo.traverse_graph(project_id="p1", node_id="run-1", depth=2)
    assert any(n.id == "t1" for n in graph.nodes)
    assert any(n.id == "t2" for n in graph.nodes)


@async_test
async def test_contradiction_detection(repo: LocalGraphAdapter):
    await repo.create_project(Project(id="p1", name="Project 1"))

    claim1 = Claim(
        id="c1",
        project_id="p1",
        text="TAM is $5B with 40% CAGR according to EdTech Report 2026",
        confidence=0.85,
    )
    claim2 = Claim(
        id="c2",
        project_id="p1",
        text="TAM is capped at $800M due to saturation in K-12",
        confidence=0.75,
    )

    await repo.save_claim(claim1)
    await repo.save_claim(claim2)

    await repo.record_contradiction(
        claim_a_id="c1",
        claim_b_id="c2",
        notes="Conflicting market size estimates between general edtech and K-12 segment.",
    )

    contradictions = await repo.find_contradictions(project_id="p1")
    assert len(contradictions) == 1
    assert contradictions[0]["claim_a_id"] == "c1"
    assert contradictions[0]["claim_b_id"] == "c2"

    c1_fetched = await repo.get_claim("c1")
    assert c1_fetched is not None
    assert c1_fetched.status == "contradicted"
