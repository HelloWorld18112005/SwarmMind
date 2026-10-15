import asyncio
from functools import wraps
import pytest
from app.graph.local_adapter import LocalGraphAdapter
from app.memory.service import MemoryService
from app.schemas.project import Project
from app.schemas.claim import Claim


def async_test(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper


@pytest.fixture
def service():
    repo = LocalGraphAdapter()
    asyncio.run(repo.initialize())
    yield MemoryService(repo)
    asyncio.run(repo.close())


@async_test
async def test_conflict_detection_and_preservation(service: MemoryService):
    await service.repo.create_project(Project(id="p-conflicts", name="Conflict Test"))

    claim1 = Claim(
        id="c1",
        project_id="p-conflicts",
        text="Market size is $5.2B in B2C tutoring",
        confidence=0.88,
    )
    claim2 = Claim(
        id="c2",
        project_id="p-conflicts",
        text="Market size is $800M ceiling due to district budgets",
        confidence=0.82,
    )

    await service.repo.save_claim(claim1)
    await service.repo.save_claim(claim2)

    # Register contradiction
    await service.record_contradiction(
        claim_a_id="c1",
        claim_b_id="c2",
        notes="B2C vs K-12 institutional TAM contradiction",
    )

    conflicts = await service.get_conflicts("p-conflicts")
    assert len(conflicts) == 1
    assert conflicts[0]["claim_a_id"] == "c1"
    assert conflicts[0]["claim_b_id"] == "c2"
    assert "B2C vs K-12" in conflicts[0]["notes"]
