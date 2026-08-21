from __future__ import annotations

from sqlalchemy import JSON, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class EmbeddingRecord(TimestampMixin, Base):
    """Stored embedding vector (JSON floats) — swappable for pgvector later."""

    __tablename__ = "embeddings"
    __table_args__ = (
        UniqueConstraint("entity_type", "entity_id", "model", name="uq_embedding_entity_model"),
    )

    entity_type: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    workspace_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    model: Mapped[str] = mapped_column(String(200), nullable=False)
    dim: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    vector: Mapped[list] = mapped_column(JSON, default=list, nullable=False)  # type: ignore[assignment]
    content_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
