"""Deterministic hash-based mock embeddings (256-dim)."""
from __future__ import annotations

import hashlib
import math


class MockEmbeddingProvider:
    """Token-hash bucket embeddings — deterministic, no downloads needed."""

    name = "mock"
    model = "mock-hash-256"
    dim = 256

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(t) for t in texts]

    def _embed_one(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        tokens = text.lower().split()
        for tok in tokens:
            digest = hashlib.md5(tok.encode("utf-8")).digest()
            idx = int.from_bytes(digest[:4], "little") % self.dim
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vec[idx] += sign
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]
