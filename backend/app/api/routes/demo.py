from typing import Any
from fastapi import APIRouter, Query
from app.dependencies import GraphRepoDep
from app.demo.seed_data import seed_demo_project, seed_incident_demo_project, seed_all_demo_projects

router = APIRouter(prefix="/demo", tags=["Demo"])


@router.post("/seed", summary="Seed demo projects into the active graph")
async def seed_demo(
    repo: GraphRepoDep,
    scenario: str = Query("venture_audit", description="Scenario to seed: 'venture_audit', 'incident', or 'all'"),
) -> dict[str, Any]:
    if scenario == "incident":
        return await seed_incident_demo_project(repo)
    elif scenario == "all":
        return await seed_all_demo_projects(repo)
    else:
        return await seed_demo_project(repo)


@router.post("/clear", summary="Clear and reset all graph and project data")
async def clear_demo(repo: GraphRepoDep) -> dict[str, str]:
    await repo.clear_all()
    return {"status": "cleared", "message": "All workspace graph data reset successfully."}
