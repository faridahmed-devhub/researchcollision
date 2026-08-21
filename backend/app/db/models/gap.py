from __future__ import annotations

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, gen_uuid, TimestampMixin


class ResearchGap(TimestampMixin, Base):
    """A research gap detected from literature â€” always evidence-backed."""

    __tablename__ = "research_gaps"

    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False
    )
    job_id: Mapped[str | None] = mapped_column(
        ForeignKey("research_jobs.id", ondelete="SET NULL"), nullable=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    gap_type: Mapped[str] = mapped_column(String(60), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="INFERRED", nullable=False)

    evidence_links = relationship(
        "ResearchGapEvidence", back_populates="gap", cascade="all, delete-orphan"
    )


class ResearchGapEvidence(Base):
    __tablename__ = "research_gap_evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    gap_id: Mapped[str] = mapped_column(
        ForeignKey("research_gaps.id", ondelete="CASCADE"), index=True, nullable=False
    )
    evidence_id: Mapped[str] = mapped_column(
        ForeignKey("evidence.id", ondelete="CASCADE"), index=True, nullable=False
    )

    gap = relationship("ResearchGap", back_populates="evidence_links")

