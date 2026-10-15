from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

ClaimStatus = Literal["proposed", "supported", "challenged", "contradicted", "verified"]


class Source(BaseModel):
    id: str
    title: str
    uri: str = ""
    source_type: str = "document"
    metadata: dict[str, str] = Field(default_factory=dict)


class ClaimCreate(BaseModel):
    text: str = Field(..., min_length=1)
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    agent_id: str | None = None
    agent_role: str | None = None
    source_ids: list[str] = Field(default_factory=list)
    memory_ids: list[str] = Field(default_factory=list)


class Claim(BaseModel):
    id: str
    project_id: str
    run_id: str | None = None
    agent_id: str | None = None
    agent_role: str | None = None
    text: str
    confidence: float = 0.7
    status: ClaimStatus = "proposed"
    supporting_source_ids: list[str] = Field(default_factory=list)
    contradicting_claim_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
