from typing import Literal
from pydantic import BaseModel, Field

AgentRole = Literal[
    "coordinator",
    "researcher",
    "analyst",
    "critic",
    "planner",
    "synthesizer",
]

AgentStatus = Literal["idle", "thinking", "executing", "waiting", "completed", "error"]


class Agent(BaseModel):
    id: str
    role: AgentRole
    name: str
    status: AgentStatus = "idle"
    current_task_id: str | None = None
    step_count: int = 0
