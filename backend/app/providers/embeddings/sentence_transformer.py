"""Sentence-Transformers embedding provider (lazy import; optional dependency)."""
from __future__ import annotations

import threading


class SentenceTransformerProvider:
    name = "sentence_transformer"

    def __init__(self, model_name: str | None = None) -> None:
        from app.core.config import settings

        self.model = settings.embedding_model or model_name or "sentence-transformers/all-MiniLM-L6-v2"
        self._model = None
        self._lock = threading.Lock()

    def _load(self):
        if self._model is None:
            with self._lock:
                if self._model is None:
                    try:
                        from sentence_transformers import SentenceTransformer
                    except ImportError as exc:  # pragma: no cover
                        raise RuntimeError(
                            "sentence-transformers is not installed. "
                            "Run: pip install sentence-transformers"
                        ) from exc
                    self._model = SentenceTransformer(self.model)
        return self._model

    async def embed(self, texts: list[str]) -> list[list[float]]:
        model = self._load()
        vectors = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
        return [v.tolist() for v in vectors]
