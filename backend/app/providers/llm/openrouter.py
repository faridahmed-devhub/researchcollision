"""OpenRouter provider (OpenAI-compatible endpoint with its own auth header)."""
from __future__ import annotations

from app.core.config import settings
from app.providers.llm.openai_compatible import OpenAICompatibleProvider


class OpenRouterProvider(OpenAICompatibleProvider):
    name = "openrouter"

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        super().__init__(
            api_key=api_key or settings.openrouter_api_key,
            model=model or settings.llm_model or "openai/gpt-4o-mini",
            base_url="https://openrouter.ai/api/v1",
        )
