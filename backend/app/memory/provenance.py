from datetime import datetime
from pydantic import BaseModel, Field


class ProvenanceRecord(BaseModel):
    """Provenance metadata tracking origins of findings, claims, and decisions."""
    agent_id: str | None = None
    agent_role: str | None = None
    task_id: str | None = None
    source_ids: list[str] = Field(default_factory=list)
    confidence: float = 0.8
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def to_metadata(self) -> dict[str, str]:
        return {
            "agent_id": self.agent_id or "unknown",
            "agent_role": self.agent_role or "unknown",
            "task_id": self.task_id or "",
            "confidence": str(self.confidence),
            "created_at": self.created_at.isoformat(),
        }
