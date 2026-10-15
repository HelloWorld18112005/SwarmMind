import asyncio
from app.graph.local_adapter import LocalGraphAdapter
from app.demo.seed_data import seed_demo_project
from app.services.explainability_service import ExplainabilityService


def async_test(coro):
    def wrapper(*args, **kwargs):
        return asyncio.run(coro(*args, **kwargs))
    return wrapper


@async_test
async def test_explainability_service_narrative():
    repo = LocalGraphAdapter()
    await repo.initialize()
    await seed_demo_project(repo)

    service = ExplainabilityService(repo)
    explanation = await service.explain_decision(
        project_id="proj-ai-tutoring",
        run_id="run-ai-tutoring-eval",
        target_title="Launch Direct-to-Consumer Parent Tier First",
    )

    assert explanation is not None
    assert len(explanation.steps) >= 3
    assert len(explanation.subgraph.nodes) >= 3
    assert "TAM" in explanation.narrative_explanation or "dispute" in explanation.narrative_explanation
    assert any(s.agent_role == "critic" for s in explanation.steps)
    assert any(s.agent_role == "researcher" for s in explanation.steps)


@async_test
async def test_shortest_path_traversal():
    repo = LocalGraphAdapter()
    await repo.initialize()
    await seed_demo_project(repo)

    # Find shortest path between a claim and a cited source
    path = await repo.find_shortest_path("proj-ai-tutoring", "claim-tam-bull", "src-edtech-tam-2026")
    assert path is not None
    assert len(path.nodes) >= 2
    assert len(path.edges) >= 1


@async_test
async def test_disputes_with_evidence():
    repo = LocalGraphAdapter()
    await repo.initialize()
    await seed_demo_project(repo)

    disputes = await repo.get_disputes_with_evidence("proj-ai-tutoring")
    assert len(disputes) >= 1
    d = disputes[0]
    assert "claim_a_text" in d
    assert "claim_b_text" in d
    assert "5.2B" in d["claim_a_text"] or "5.2B" in d["claim_b_text"]
    assert "800M" in d["claim_a_text"] or "800M" in d["claim_b_text"]
