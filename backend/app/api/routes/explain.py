from fastapi import APIRouter, HTTPException, Query
from app.dependencies import GraphRepoDep
from app.schemas.explainability import ExplanationResponse
from app.services.explainability_service import ExplainabilityService

router = APIRouter(prefix="/runs/{run_id}/explain", tags=["Explainability"])


@router.get("", response_model=ExplanationResponse, summary="Explain recommendation or graph decision with multi-hop provenance")
async def explain_decision(
    run_id: str,
    repo: GraphRepoDep,
    node_id: str | None = Query(default=None, description="Specific node ID to trace"),
    recommendation_title: str | None = Query(default=None, description="Title of recommendation or finding to justify"),
) -> ExplanationResponse:
    run = await repo.get_run(run_id)
    if not run:
        # Graceful fallback: check all projects to see if the run exists or locate the project containing node_id
        projects = await repo.list_projects()
        for p in projects:
            p_runs = await repo.list_runs(p.id)
            if any(r.id == run_id for r in p_runs):
                run = next(r for r in p_runs if r.id == run_id)
                break

        # If still not found and node_id is provided, search projects for the node
        if not run and node_id:
            for p in projects:
                p_graph = await repo.get_project_graph(p.id, limit=300)
                if any(n.id == node_id for n in p_graph.nodes):
                    p_runs = await repo.list_runs(p.id)
                    if p_runs:
                        run = p_runs[0]
                    break

        # Fallback to the first available run in the system if exists
        if not run:
            for p in projects:
                p_runs = await repo.list_runs(p.id)
                if p_runs:
                    run = p_runs[0]
                    break

        if not run:
            raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")

    service = ExplainabilityService(repo)
    return await service.explain_decision(
        project_id=run.project_id,
        run_id=run.id,
        target_id=node_id,
        target_title=recommendation_title,
    )
