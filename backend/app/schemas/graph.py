from typing import Any
from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    id: str
    label: str = Field(..., description="Node type: Project, Run, Agent, Task, Memory, Claim, Source, Decision, Artifact")
    title: str = Field(..., description="Display title / label")
    properties: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    id: str
    source: str = Field(..., description="Source node id")
    target: str = Field(..., description="Target node id")
    relationship: str = Field(..., description="Relationship type: OWNS, HAS_RUN, PRODUCED, SUPPORTS, CONTRADICTS, etc.")
    properties: dict[str, Any] = Field(default_factory=dict)


class GraphData(BaseModel):
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)


class GraphPath(BaseModel):
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
    explanation: str = ""
