import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, status
from app.dependencies import GraphRepoDep
from app.schemas.project import Project, ProjectCreate, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("", response_model=Project, status_code=status.HTTP_201_CREATED, summary="Create a new workspace project")
async def create_project(payload: ProjectCreate, repo: GraphRepoDep) -> Project:
    project_id = f"proj-{uuid.uuid4().hex[:8]}"
    project = Project(
        id=project_id,
        name=payload.name,
        description=payload.description,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    return await repo.create_project(project)


@router.get("", response_model=list[Project], summary="List all workspace projects")
async def list_projects(repo: GraphRepoDep) -> list[Project]:
    return await repo.list_projects()


@router.get("/{project_id}", response_model=Project, summary="Get project details")
async def get_project(project_id: str, repo: GraphRepoDep) -> Project:
    project = await repo.get_project(project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{project_id}' not found")
    return project


@router.patch("/{project_id}", response_model=Project, summary="Update project")
async def update_project(project_id: str, payload: ProjectUpdate, repo: GraphRepoDep) -> Project:
    updated = await repo.update_project(project_id, payload)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{project_id}' not found")
    return updated


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete project")
async def delete_project(project_id: str, repo: GraphRepoDep) -> None:
    deleted = await repo.delete_project(project_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project '{project_id}' not found")
