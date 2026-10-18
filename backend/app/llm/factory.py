from app.config import Settings, get_settings
from app.llm.base import LLMProvider
from app.llm.providers.mock_provider import MockProvider
from app.llm.providers.gemini_provider import GeminiProvider
from app.llm.providers.openai_provider import OpenAIProvider

_llm_instance: LLMProvider | None = None


def create_llm_provider(settings: Settings | None = None) -> LLMProvider:
    """Factory instantiating the configured LLM provider."""
    cfg = settings or get_settings()
    provider_type = cfg.llm_provider.lower()

    if provider_type == "mock":
        return MockProvider(model_name=cfg.llm_model or "mock-model")

    if provider_type == "gemini":
        return GeminiProvider(api_key=cfg.llm_api_key, model=cfg.llm_model or "gemini-2.5-flash")

    if provider_type == "openai":
        return OpenAIProvider(api_key=cfg.llm_api_key, model=cfg.llm_model or "gpt-4o-mini")

    raise ValueError(f"Unsupported LLM provider: '{provider_type}'. Supported: 'mock', 'gemini', 'openai'.")


def get_llm_provider() -> LLMProvider:
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = create_llm_provider()
    return _llm_instance
