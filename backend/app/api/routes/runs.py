import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, status
from app.dependencies import GraphRepoDep
from app.schemas.run import Run, RunCreate
from app.schemas.task import Task
from app.schemas.claim import Claim
from app.orchestration.engine import get_orchestration_engine

router = APIRouter(tags=["Investigations & Runs"])


@router.post("/projects/{project_id}/runs", response_model=Run, status_code=status.HTTP_201_CREATED, summary="Start an investigation run")
async def create_run(project_id: str, payload: RunCreate, repo: GraphRepoDep) -> Run:
    project = await repo.get_project(project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{project_id}' not found")

    run_id = f"run-{uuid.uuid4().hex[:8]}"
    run = Run(
        id=run_id,
        project_id=project_id,
        goal=payload.goal,
        status="pending",
        started_at=datetime.utcnow(),
    )
    created = await repo.create_run(run)

    # Launch multi-agent swarm in background
    engine = await get_orchestration_engine()
    engine.start_background_run(run_id)

    return created


@router.get("/projects/{project_id}/runs", response_model=list[Run], summary="List runs in project")
async def list_runs(project_id: str, repo: GraphRepoDep) -> list[Run]:
    return await repo.list_runs(project_id)


@router.get("/runs/{run_id}", response_model=Run, summary="Get run status")
async def get_run(run_id: str, repo: GraphRepoDep) -> Run:
    run = await repo.get_run(run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Run '{run_id}' not found")
    return run


@router.post("/runs/{run_id}/cancel", summary="Cancel active run")
async def cancel_run(run_id: str) -> dict[str, str]:
    engine = await get_orchestration_engine()
    success = await engine.cancel_run(run_id)
    return {"status": "cancelled" if success else "not_found"}


@router.get("/runs/{run_id}/tasks", response_model=list[Task], summary="List tasks in run")
async def list_run_tasks(run_id: str, repo: GraphRepoDep) -> list[Task]:
    return await repo.list_tasks(run_id)


@router.get("/runs/{run_id}/claims", response_model=list[Claim], summary="List claims and disputes in run")
async def list_run_claims(run_id: str, repo: GraphRepoDep) -> list[Claim]:
    run = await repo.get_run(run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Run '{run_id}' not found")
    return await repo.list_claims(project_id=run.project_id, run_id=run_id)
