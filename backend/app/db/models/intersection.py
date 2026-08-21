from __future__ import annotations

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import DiscoveryMode
from app.db.base import Base, gen_uuid, TimestampMixin


class ResearchIntersection(TimestampMixin, Base):
    """The core product object: a discovered research intersection."""

    __tablename__ = "research_intersections"

    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False
    )
    job_id: Mapped[str | None] = mapped_column(
        ForeignKey("research_jobs.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(400), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    shared_problem: Mapped[str | None] = mapped_column(Text, nullable=True)
    complementary_expertise: Mapped[str | None] = mapped_column(Text, nullable=True)
    research_gap_id: Mapped[str | None] = mapped_column(
        ForeignKey("research_gaps.id", ondelete="SET NULL"), nullable=True
    )
    gap_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    researcher_a_id: Mapped[str] = mapped_column(
        ForeignKey("researchers.id", ondelete="CASCADE"), index=True, nullable=False
    )
    researcher_b_id: Mapped[str] = mapped_column(
        ForeignKey("researchers.id", ondelete="CASCADE"), index=True, nullable=False
    )
    why_researcher_a: Mapped[str | None] = mapped_column(Text, nullable=True)
    why_researcher_b: Mapped[str | None] = mapped_column(Text, nullable=True)

    novelty_confidence: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    feasibility_confidence: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    discovery_mode: Mapped[str] = mapped_column(
        String(20), default=DiscoveryMode.NORMAL.value, nullable=False
    )
    status: Mapped[str] = mapped_column(String(30), default="suggested", nullable=False)

    evidence_links = relationship(
        "IntersectionEvidence", back_populates="intersection", cascade="all, delete-orphan"
    )


class IntersectionEvidence(Base):
    __tablename__ = "intersection_evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    intersection_id: Mapped[str] = mapped_column(
        ForeignKey("research_intersections.id", ondelete="CASCADE"), index=True, nullable=False
    )
    evidence_id: Mapped[str] = mapped_column(
        ForeignKey("evidence.id", ondelete="CASCADE"), index=True, nullable=False
    )

    intersection = relationship("ResearchIntersection", back_populates="evidence_links")

