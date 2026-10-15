from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

RunStatus = Literal["pending", "running", "paused", "completed", "failed", "cancelled"]


class RunCreate(BaseModel):
    goal: str = Field(..., min_length=5, max_length=5000, description="Investigation goal or research prompt")


class Run(BaseModel):
    id: str
    project_id: str
    goal: str
    status: RunStatus = "pending"
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    task_count: int = 0
    completed_task_count: int = 0
    findings_count: int = 0
    conflicts_count: int = 0
