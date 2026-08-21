from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import EvidenceStatus
from app.db.base import Base, TimestampMixin


class Evidence(TimestampMixin, Base):
    """A traceable evidence item backing an AI-generated claim."""

    __tablename__ = "evidence"

    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False
    )
    claim: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(600), nullable=True)
    source_type: Mapped[str] = mapped_column(String(40), default="paper_abstract", nullable=False)
    paper_id: Mapped[str | None] = mapped_column(
        ForeignKey("papers.id", ondelete="CASCADE"), index=True, nullable=True
    )
    source_title: Mapped[str | None] = mapped_column(String(600), nullable=True)
    evidence_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default=EvidenceStatus.UNVERIFIED.value, nullable=False
    )
    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
