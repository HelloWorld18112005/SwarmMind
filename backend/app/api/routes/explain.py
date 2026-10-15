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
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")

    service = ExplainabilityService(repo)
    return await service.explain_decision(
        project_id=run.project_id,
        run_id=run_id,
        target_id=node_id,
        target_title=recommendation_title,
    )
