from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class TurnCreate(BaseModel):
    content: str = Field(..., min_length=1, description="Message text from user or agent")
    role: Literal["user", "assistant", "agent", "system"] = "user"
    mentioned_claim_ids: list[str] = Field(default_factory=list, description="IDs of claims or memories referenced in this turn")


class Turn(BaseModel):
    id: str
    run_id: str
    role: str
    content: str
    prev_turn_id: str | None = None
    mentioned_claim_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    role: Literal["user", "agent"] = "user"


class ChatResponse(BaseModel):
    user_turn: Turn
    assistant_turn: Turn | None = None
    mentioned_claims: list[dict[str, str]] = Field(default_factory=list)
