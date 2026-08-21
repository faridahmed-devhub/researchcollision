"""Embedding provider factory."""
from __future__ import annotations

from app.core.config import settings
from app.providers.embeddings.base import EmbeddingProvider
from app.providers.embeddings.mock import MockEmbeddingProvider


def get_embedding_provider() -> EmbeddingProvider:
    if settings.embedding_provider == "mock":
        return MockEmbeddingProvider()
    if settings.embedding_provider == "sentence_transformer":
        from app.providers.embeddings.sentence_transformer import SentenceTransformerProvider

        try:
            return SentenceTransformerProvider()
        except Exception:
            return MockEmbeddingProvider()
    return MockEmbeddingProvider()
