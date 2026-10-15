from fastapi import APIRouter
from app.api.routes import health, projects, runs, memories, graph, demo, events, reports, explain, budgets

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(projects.router)
api_router.include_router(runs.router)
api_router.include_router(memories.router)
api_router.include_router(graph.router)
api_router.include_router(demo.router)
api_router.include_router(events.router)
api_router.include_router(reports.router)
api_router.include_router(explain.router)
api_router.include_router(budgets.router)
