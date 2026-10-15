from typing import Any
from fastapi import APIRouter
from app.dependencies import GraphRepoDep
from app.demo.seed_data import seed_demo_project

router = APIRouter(prefix="/demo", tags=["Demo"])


@router.post("/seed", summary="Seed the Signature Demo project into the active graph")
async def seed_demo(repo: GraphRepoDep) -> dict[str, Any]:
    return await seed_demo_project(repo)
