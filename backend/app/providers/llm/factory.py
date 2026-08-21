"""LLM provider factory."""
from __future__ import annotations

from app.core.config import settings
from app.providers.llm.base import LLMProvider
from app.providers.llm.mock import MockLLMProvider
from app.providers.llm.openai_compatible import OpenAICompatibleProvider
from app.providers.llm.openrouter import OpenRouterProvider


def get_llm_provider() -> LLMProvider:
    """Return the configured provider; falls back to mock without credentials."""
    if settings.is_mock_llm:
        return MockLLMProvider()
    if settings.llm_provider == "openrouter":
        return OpenRouterProvider()
    if settings.llm_provider == "openai_compatible":
        return OpenAICompatibleProvider()
    return MockLLMProvider()
