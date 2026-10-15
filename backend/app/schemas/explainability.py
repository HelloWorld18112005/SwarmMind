from typing import Any
from pydantic import BaseModel, Field
from app.schemas.graph import GraphData


class ExplainabilityStep(BaseModel):
    step_number: int
    agent_role: str
    action: str
    finding: str
    confidence: float = 1.0
    source_citation: str | None = None


class ExplanationResponse(BaseModel):
    target_id: str
    target_title: str
    confidence_assessment: str
    narrative_explanation: str
    steps: list[ExplainabilityStep] = Field(default_factory=list)
    sources: list[dict[str, Any]] = Field(default_factory=list)
    contradictions: list[dict[str, Any]] = Field(default_factory=list)
    subgraph: GraphData = Field(default_factory=GraphData)
