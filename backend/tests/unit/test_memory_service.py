import asyncio
from functools import wraps
import pytest
from app.graph.local_adapter import LocalGraphAdapter
from app.memory.service import MemoryService
from app.schemas.project import Project
from app.schemas.memory import MemoryCreate
from app.schemas.claim import ClaimCreate


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
async def test_memory_creation_and_deduplication(service: MemoryService):
    p = Project(id="p-mem", name="Memory Project")
    await service.repo.create_project(p)

    payload = MemoryCreate(
        content="Direct-to-consumer AI tutoring TAM is $5.2B according to industry reports",
        memory_type="fact",
        confidence=0.85,
    )

    # 1. Save initial memory
    mem1, is_new = await service.save_memory("p-mem", payload)
    assert is_new is True
    assert mem1.content == payload.content

    # 2. Save identical memory -> should detect duplicate
    mem2, is_new2 = await service.save_memory("p-mem", payload, check_duplicates=True)
    assert is_new2 is False
    assert mem2.id == mem1.id

    # 3. Query memories
    memories = await service.list_memories("p-mem", query="tutoring")
    assert len(memories) == 1


@async_test
async def test_claim_provenance_and_traversal(service: MemoryService):
    p = Project(id="p-prov", name="Provenance Project")
    await service.repo.create_project(p)

    claim_payload = ClaimCreate(
        text="Voice latency below 400ms is essential for student immersion",
        confidence=0.9,
        source_ids=["src-1"],
    )

    claim = await service.create_claim("p-prov", claim_payload)
    assert claim.id.startswith("claim-")

    # Traverse path from claim
    path = await service.traverse_path("p-prov", node_id=claim.id, depth=1)
    assert len(path.nodes) >= 1
