from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import get_settings
from app.graph.factory import get_graph_repository, close_graph_repository

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("swarmmind")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    logger.info(f"Starting SwarmMind API in '{settings.app_env}' mode...")
    logger.info(f"Configured Graph Backend: '{settings.graph_backend}'")

    try:
        repo = await get_graph_repository()
        health = await repo.check_health()
        logger.info(f"Graph Repository ready: {health}")
    except Exception as e:
        logger.error(f"Failed to initialize graph repository: {e}")
        if settings.graph_backend == "falkordb":
            raise

    yield

    logger.info("Shutting down SwarmMind API...")
    await close_graph_repository()
    logger.info("Graph connections closed successfully.")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="SwarmMind API",
        description="Graph-grounded multi-agent AI collaboration platform API",
        version="0.1.0",
        lifespan=lifespan,
    )

    origins = [
        settings.frontend_origin,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api")

    @app.get("/", summary="Root Status")
    async def root() -> dict[str, str]:
        return {
            "app": "SwarmMind",
            "version": "0.1.0",
            "description": "Graph-powered multi-agent AI collaboration platform",
            "docs": "/docs",
            "health": "/api/health",
        }

    return app


app = create_app()
