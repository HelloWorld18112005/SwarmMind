from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

MemoryType = Literal[
    "semantic",
    "episodic",
    "procedural",
    "fact",
    "observation",
    "rule",
    "hypothesis",
    "summary",
]


class MemoryCreate(BaseModel):
    content: str = Field(..., min_length=1, description="Knowledge content")
    memory_type: MemoryType = "semantic"
    instruction: str | None = Field(default=None, description="Operational rule instruction for procedural memories")
    agent_id: str | None = None
    agent_role: str | None = None
    task_id: str | None = None
    source_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    tags: list[str] = Field(default_factory=list)
    valid_at: datetime | None = None
    invalid_at: datetime | None = None


class MemoryUpdate(BaseModel):
    content: str | None = None
    memory_type: MemoryType | None = None
    instruction: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    valid_at: datetime | None = None
    invalid_at: datetime | None = None
    successes: int | None = None
    failures: int | None = None


class Memory(BaseModel):
    id: str
    project_id: str
    run_id: str | None = None
    agent_id: str | None = None
    agent_role: str | None = None
    task_id: str | None = None
    content: str
    memory_type: MemoryType = "semantic"
    instruction: str | None = None
    confidence: float = 0.8
    successes: int = 0
    failures: int = 0
    tags: list[str] = Field(default_factory=list)
    valid_at: datetime | None = None
    invalid_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
