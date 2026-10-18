"""FastMCP Tool Server for SwarmMind Graph Intelligence."""

from typing import Any
import logging
from mcp.server.fastmcp import FastMCP
from app.graph.factory import get_graph_repository
from app.memory.service import MemoryService
from app.agents.tools.evidence import EvidenceTool
from app.schemas.claim import ClaimCreate

logger = logging.getLogger(__name__)

mcp = FastMCP(
    name="SwarmMind-Graph-Intelligence",
    instructions="SwarmMind graph memory and native FalkorDB intelligence tools.",
)


@mcp.tool()
async def search_graph_memories(project_id: str, query: str = "", limit: int = 20) -> list[dict[str, Any]]:
    """Search project memories in the shared graph memory.
    
    Args:
        project_id: The ID of the tenant project.
        query: Optional text filter.
        limit: Max number of memories to return.
    """
    repo = await get_graph_repository()
    service = MemoryService(repo)
    memories = await service.list_memories(project_id=project_id, query=query or None, limit=limit)
    return [
        {
            "id": m.id,
            "content": m.content,
            "memory_type": m.memory_type,
            "confidence": m.confidence,
            "instruction": m.instruction,
            "created_at": m.created_at.isoformat(),
        }
        for m in memories
    ]


@mcp.tool()
async def rank_evidence_authority(project_id: str, limit: int = 5) -> list[dict[str, Any]]:
    """Rank project claims by centrality using native FalkorDB PageRank (algo.pageRank).
    
    Args:
        project_id: The ID of the tenant project.
        limit: Max number of top claims to return.
    """
    repo = await get_graph_repository()
    service = MemoryService(repo)
    tool = EvidenceTool(service)
    return await tool.rank_evidence_authority(project_id=project_id, limit=limit)


@mcp.tool()
async def trace_shortest_path(project_id: str, claim_a_id: str, claim_b_id: str) -> list[str]:
    """Trace explainable shortest path between two claims using native FalkorDB SPpaths (algo.SPpaths).
    
    Args:
        project_id: The ID of the tenant project.
        claim_a_id: Start claim ID.
        claim_b_id: Target claim ID.
    """
    repo = await get_graph_repository()
    service = MemoryService(repo)
    tool = EvidenceTool(service)
    return await tool.trace_shortest_path(project_id=project_id, claim_a_id=claim_a_id, claim_b_id=claim_b_id)


@mcp.tool()
async def get_disputes_with_evidence(project_id: str) -> list[dict[str, Any]]:
    """Retrieve all conflicting claims and evidence citations in the project graph.
    
    Args:
        project_id: The ID of the tenant project.
    """
    repo = await get_graph_repository()
    return await repo.get_disputes_with_evidence(project_id)


@mcp.tool()
async def record_claim_evidence(
    project_id: str,
    text: str,
    confidence: float = 0.85,
    agent_role: str = "analyst",
) -> dict[str, Any]:
    """Record a verified empirical finding or claim into the project graph.
    
    Args:
        project_id: The ID of the tenant project.
        text: The factual claim or observation.
        confidence: Confidence score between 0.0 and 1.0.
        agent_role: The role of the agent generating the claim.
    """
    repo = await get_graph_repository()
    service = MemoryService(repo)
    claim = await service.create_claim(
        project_id=project_id,
        payload=ClaimCreate(text=text, confidence=confidence, agent_role=agent_role),
    )
    return {"id": claim.id, "text": claim.text, "confidence": claim.confidence, "status": claim.status}
