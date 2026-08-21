"""Vector service: embedding storage + cosine similarity (pgvector-swappable)."""
from __future__ import annotations

import hashlib

import numpy as np
import structlog
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import EmbeddingRecord
from app.providers.embeddings.factory import get_embedding_provider

logger = structlog.get_logger(__name__)


class VectorService:
    """Stores embeddings in SQLite; the interface can move to pgvector later."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.provider = get_embedding_provider()

    @staticmethod
    def content_hash(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    async def embed_and_store(
        self,
        *,
        entity_type: str,
        entity_id: str,
        text: str,
        workspace_id: str | None = None,
    ) -> EmbeddingRecord:
        """Embed text and upsert. Skips re-embedding when content unchanged."""
        c_hash = self.content_hash(text)
        existing = self.db.scalar(
            select(EmbeddingRecord).where(
                EmbeddingRecord.entity_type == entity_type,
                EmbeddingRecord.entity_id == entity_id,
                EmbeddingRecord.model == self.provider.model,
            )
        )
        if existing and existing.content_hash == c_hash:
            return existing  # cache hit — do not re-embed
        vector = (await self.provider.embed([text]))[0]
        if existing:
            existing.vector = vector
            existing.dim = len(vector)
            existing.content_hash = c_hash
            self.db.flush()
            return existing
        record = EmbeddingRecord(
            entity_type=entity_type,
            entity_id=entity_id,
            workspace_id=workspace_id,
            model=self.provider.model,
            dim=len(vector),
            vector=vector,
            content_hash=c_hash,
        )
        self.db.add(record)
        self.db.flush()
        return record

    def similarity_search(
        self,
        *,
        query_vector: list[float],
        workspace_id: str | None = None,
        entity_types: list[str] | None = None,
        top_k: int = 10,
    ) -> list[tuple[str, str, float]]:
        """Return [(entity_type, entity_id, score)] sorted by cosine similarity."""
        stmt = select(EmbeddingRecord)
        if workspace_id:
            stmt = stmt.where(
                (EmbeddingRecord.workspace_id == workspace_id)
                | (EmbeddingRecord.workspace_id.is_(None))
            )
        if entity_types:
            stmt = stmt.where(EmbeddingRecord.entity_type.in_(entity_types))
        rows = list(self.db.scalars(stmt))
        if not rows:
            return []
        q = np.asarray(query_vector, dtype=np.float32)
        q_norm = np.linalg.norm(q) or 1.0
        results: list[tuple[str, str, float]] = []
        for r in rows:
            v = np.asarray(r.vector, dtype=np.float32)
            denom = (np.linalg.norm(v) * q_norm) or 1.0
            score = float(np.dot(q, v) / denom)
            results.append((r.entity_type, r.entity_id, score))
        results.sort(key=lambda t: -t[2])
        return results[:top_k]

    async def search_text(
        self, query: str, *, workspace_id: str | None = None, top_k: int = 10,
        entity_types: list[str] | None = None,
    ) -> list[tuple[str, str, float]]:
        qv = (await self.provider.embed([query]))[0]
        return self.similarity_search(
            query_vector=qv, workspace_id=workspace_id, entity_types=entity_types, top_k=top_k
        )


def get_model_name() -> str:
    return settings.embedding_model
