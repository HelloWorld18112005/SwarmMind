from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field
from app.schemas.agent import AgentRole

TaskStatus = Literal["pending", "ready", "running", "completed", "failed", "cancelled"]
TaskPriority = Literal["low", "medium", "high", "critical"]


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(default="")
    assigned_role: AgentRole
    priority: TaskPriority = "medium"
    dependencies: list[str] = Field(default_factory=list, description="IDs of prerequisite tasks")


class Task(BaseModel):
    id: str
    run_id: str
    title: str
    description: str = ""
    assigned_role: AgentRole
    assigned_agent_id: str | None = None
    status: TaskStatus = "pending"
    priority: TaskPriority = "medium"
    dependencies: list[str] = Field(default_factory=list)
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None
