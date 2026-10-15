import asyncio
from app.graph.local_adapter import LocalGraphAdapter
from app.memory.service import MemoryService
from app.schemas.project import Project
from app.schemas.memory import MemoryCreate
from app.schemas.claim import ClaimCreate
from app.security.redaction import redact_sensitive_data, contains_sensitive_data
from app.security.sanitization import sanitize_identifier, validate_query_parameters
import pytest


def async_test(coro):
    def wrapper(*args, **kwargs):
        return asyncio.run(coro(*args, **kwargs))
    return wrapper


def test_secret_redaction_patterns():
    # OpenAI key
    text1 = "Here is my secret sk-abcdef12345678901234567890 in the prompt"
    redacted1 = redact_sensitive_data(text1)
    assert "sk-abcdef1234567890" not in redacted1
    assert "REDACTED" in redacted1

    # Gemini key
    text2 = "Using Gemini key AIzaSyA1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6Q"
    redacted2 = redact_sensitive_data(text2)
    assert "AIzaSyA1B2C3" not in redacted2
    assert "REDACTED" in redacted2

    # Password
    text3 = "Connecting with password='super_secret_redis_pass_123'"
    redacted3 = redact_sensitive_data(text3)
    assert "super_secret_redis_pass_123" not in redacted3
    assert "REDACTED" in redacted3


@async_test
async def test_memory_service_redacts_on_save():
    repo = LocalGraphAdapter()
    await repo.initialize()
    service = MemoryService(repo)

    await repo.create_project(Project(id="p-sec", name="Security Project"))

    # Attempt to save memory containing raw API key
    saved_mem, _ = await service.save_memory(
        project_id="p-sec",
        payload=MemoryCreate(
            content="Configuration loaded with sk-secretkey12345678909876543210 and password=admin_pass_999",
            memory_type="fact",
        ),
    )

    assert "sk-secretkey123" not in saved_mem.content
    assert "admin_pass_999" not in saved_mem.content
    assert "REDACTED" in saved_mem.content


@async_test
async def test_cross_project_graph_isolation():
    repo = LocalGraphAdapter()
    await repo.initialize()
    service = MemoryService(repo)

    # Create two separate projects
    await repo.create_project(Project(id="p-alpha", name="Project Alpha"))
    await repo.create_project(Project(id="p-beta", name="Project Beta"))

    # Save sensitive data in Project Alpha
    await service.save_memory(
        project_id="p-alpha",
        payload=MemoryCreate(content="Alpha internal trade secrets", memory_type="fact"),
    )

    # Save data in Project Beta
    await service.save_memory(
        project_id="p-beta",
        payload=MemoryCreate(content="Beta public roadmap", memory_type="fact"),
    )

    # Query Project Beta memories
    beta_memories = await repo.list_memories("p-beta")
    assert len(beta_memories) == 1
    assert beta_memories[0].content == "Beta public roadmap"
    assert not any("Alpha" in m.content for m in beta_memories)

    # Query Project Beta graph
    beta_graph = await repo.get_project_graph("p-beta")
    beta_node_titles = [n.title for n in beta_graph.nodes]
    assert not any("Alpha" in t for t in beta_node_titles)


def test_cypher_sanitization_guardrails():
    # Safe identifiers
    assert sanitize_identifier("Memory") == "Memory"
    assert sanitize_identifier("SUPPORTED_BY") == "SUPPORTED_BY"

    # Malicious injection attempt
    with pytest.raises(ValueError):
        sanitize_identifier("Memory; DROP ALL;")

    with pytest.raises(ValueError):
        sanitize_identifier("Claim {id: $id}) DETACH DELETE n //")
