from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class Recommendation(BaseModel):
    title: str
    description: str
    priority: str = "medium"
    supporting_claim_ids: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    provenance_chain: list[str] = Field(default_factory=list)
    pagerank_score: float | None = None


class ConflictItem(BaseModel):
    claim_a_id: str
    claim_a_text: str
    claim_b_id: str
    claim_b_text: str
    status: str = "unresolved"
    notes: str = ""


class Report(BaseModel):
    id: str
    project_id: str
    run_id: str
    title: str
    executive_summary: str
    findings: list[str] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)
    unresolved_conflicts: list[ConflictItem] = Field(default_factory=list)
    sources: list[dict[str, Any]] = Field(default_factory=list)
    confidence_assessment: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
