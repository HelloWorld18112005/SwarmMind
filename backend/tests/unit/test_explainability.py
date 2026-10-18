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
    seed_res = await seed_demo_project(repo)
    proj_id = seed_res["project_id"]
    run_id = seed_res["run_id"]

    service = ExplainabilityService(repo)
    explanation = await service.explain_decision(
        project_id=proj_id,
        run_id=run_id,
        target_title="Valuation Adjustment: Withhold $12M in deal escrow",
    )

    assert explanation is not None
    assert len(explanation.steps) >= 3
    assert len(explanation.subgraph.nodes) >= 3
    narrative_lower = explanation.narrative_explanation.lower()
    assert any(term in narrative_lower for term in ("dispute", "proprietary", "gpl", "escrow", "apexai"))
    assert any(s.agent_role in ("critic", "researcher", "analyst", "planner", "synthesizer") for s in explanation.steps)


@async_test
async def test_shortest_path_traversal():
    repo = LocalGraphAdapter()
    await repo.initialize()
    seed_res = await seed_demo_project(repo)
    proj_id = seed_res["project_id"]

    # Find shortest path between a task and a source
    path = await repo.find_shortest_path(proj_id, "task-2-ip-audit", "src_git_bom")
    assert path is not None
    assert len(path.nodes) >= 2
    assert len(path.edges) >= 1


@async_test
async def test_disputes_with_evidence():
    repo = LocalGraphAdapter()
    await repo.initialize()
    seed_res = await seed_demo_project(repo)
    proj_id = seed_res["project_id"]

    disputes = await repo.get_disputes_with_evidence(proj_id)
    assert len(disputes) >= 1
    d = disputes[0]
    assert "claim_a_text" in d
    assert "claim_b_text" in d
    combined = " ".join(item["claim_a_text"] + " " + item["claim_b_text"] for item in disputes).lower()
    assert "gpl" in combined or "proprietary" in combined or "uptime" in combined
