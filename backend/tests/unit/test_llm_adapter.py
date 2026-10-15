import asyncio
from functools import wraps
import pytest
from app.config import Settings
from app.llm.base import ChatMessage
from app.llm.factory import create_llm_provider
from app.llm.providers.mock_provider import MockProvider


def async_test(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper


@async_test
async def test_mock_provider_generation():
    provider = MockProvider()
    resp = await provider.generate([
        ChatMessage(role="system", content="You are the coordinator agent"),
        ChatMessage(role="user", content="Decompose AI Tutoring goal"),
    ])
    assert resp.content
    assert "tasks" in resp.content
    assert resp.prompt_tokens > 0


def test_llm_factory():
    settings = Settings(llm_provider="mock", llm_model="test-mock")
    prov = create_llm_provider(settings)
    assert isinstance(prov, MockProvider)
