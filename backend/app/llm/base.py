from typing import Any, Protocol, runtime_checkable
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., description="system, user, or assistant")
    content: str = Field(..., description="Message text or JSON payload")


class LLMResponse(BaseModel):
    content: str
    raw: dict[str, Any] = Field(default_factory=dict)
    prompt_tokens: int = 0
    completion_tokens: int = 0


@runtime_checkable
class LLMProvider(Protocol):
    async def generate(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.2,
        max_tokens: int = 2000,
        response_json: bool = True,
    ) -> LLMResponse:
        """Generate a text or JSON completion from the LLM."""
        ...
