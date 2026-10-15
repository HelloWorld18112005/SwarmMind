from typing import Any
from app.graph.base import GraphRepository
from app.schemas.claim import Claim


class ConflictDetector:
    """Detects and records contradictory claims in the shared graph memory."""

    def __init__(self, repo: GraphRepository) -> None:
        self.repo = repo

    async def register_contradiction(
        self,
        claim_a_id: str,
        claim_b_id: str,
        reason: str = "Dispute or contradictory proposition detected by Critic agent",
    ) -> None:
        """Record a bidirectional CONTRADICTS relationship between two claims."""
        await self.repo.record_contradiction(
            claim_a_id=claim_a_id,
            claim_b_id=claim_b_id,
            notes=reason,
        )

    async def get_project_conflicts(self, project_id: str) -> list[dict[str, Any]]:
        """Retrieve all contradictory claims recorded in the project graph."""
        return await self.repo.find_contradictions(project_id)
