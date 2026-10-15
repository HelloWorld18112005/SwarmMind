import json
import httpx
from app.llm.base import ChatMessage, LLMProvider, LLMResponse


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider adapter using direct REST API."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        self.api_key = api_key
        self.model = model or "gpt-4o-mini"
        self.url = "https://api.openai.com/v1/chat/completions"

    async def generate(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.2,
        max_tokens: int = 2000,
        response_json: bool = True,
    ) -> LLMResponse:
        if not self.api_key:
            raise ValueError("OpenAI API key is missing. Set LLM_API_KEY in .env or switch LLM_PROVIDER=mock.")

        formatted_messages = [{"role": m.role, "content": m.content} for m in messages]
        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_json:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(self.url, json=payload, headers=headers)
            if resp.status_code != 200:
                raise RuntimeError(f"OpenAI API error ({resp.status_code}): {resp.text}")

            data = resp.json()
            choice = data["choices"][0]
            usage = data.get("usage", {})
            return LLMResponse(
                content=choice["message"]["content"],
                raw=data,
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
            )
