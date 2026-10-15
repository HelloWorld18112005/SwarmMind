import logging
from app.config import Settings, get_settings
from app.graph.base import GraphRepository
from app.graph.local_adapter import LocalGraphAdapter
from app.graph.falkordb_adapter import FalkorDBAdapter

logger = logging.getLogger(__name__)

_repository_instance: GraphRepository | None = None


def create_graph_repository(settings: Settings | None = None) -> GraphRepository:
    cfg = settings or get_settings()

    if cfg.graph_backend == "falkordb":
        logger.info(f"Using FalkorDB backend (target: {cfg.falkordb_host}:{cfg.falkordb_port}, graph: {cfg.falkordb_graph})")
        return FalkorDBAdapter(
            host=cfg.falkordb_host,
            port=cfg.falkordb_port,
            username=cfg.falkordb_username,
            password=cfg.falkordb_password,
            ssl=cfg.falkordb_ssl,
            graph_name=cfg.falkordb_graph,
        )

    if cfg.graph_backend == "local":
        logger.info("Using Local in-memory graph repository (offline development mode)")
        return LocalGraphAdapter()

    raise ValueError(f"Unknown graph backend: '{cfg.graph_backend}'. Supported options: 'local', 'falkordb'.")


async def get_graph_repository() -> GraphRepository:
    global _repository_instance
    if _repository_instance is None:
        _repository_instance = create_graph_repository()
        await _repository_instance.initialize()
    return _repository_instance


async def close_graph_repository() -> None:
    global _repository_instance
    if _repository_instance is not None:
        await _repository_instance.close()
        _repository_instance = None
