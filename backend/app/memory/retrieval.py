from typing import Any
from app.graph.base import GraphRepository
from app.schemas.graph import GraphData


class GraphRetrieval:
    """Multi-hop knowledge retrieval and graph traversal engine."""

    def __init__(self, repo: GraphRepository) -> None:
        self.repo = repo

    async def get_subgraph(
        self,
        project_id: str,
        node_types: list[str] | None = None,
        limit: int = 150,
    ) -> GraphData:
        """Retrieve project graph nodes and edges for exploration."""
        return await self.repo.get_project_graph(project_id, node_types=node_types, limit=limit)

    async def trace_provenance(
        self,
        project_id: str,
        node_id: str,
        depth: int = 2,
    ) -> GraphData:
        """Traverse relationships starting from a specific node to trace its provenance tree."""
        return await self.repo.traverse_graph(project_id=project_id, node_id=node_id, depth=depth)
