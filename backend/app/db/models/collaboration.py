from __future__ import annotations

from sqlalchemy import JSON, ForeignKey, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class CollaborationCandidate(TimestampMixin, Base):
    """Ranked collaboration pair with transparent component scores."""

    __tablename__ = "collaboration_candidates"

    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False
    )
    intersection_id: Mapped[str | None] = mapped_column(
        ForeignKey("research_intersections.id", ondelete="SET NULL"), nullable=True
    )
    researcher_a_id: Mapped[str] = mapped_column(
        ForeignKey("researchers.id", ondelete="CASCADE"), index=True, nullable=False
    )
    researcher_b_id: Mapped[str] = mapped_column(
        ForeignKey("researchers.id", ondelete="CASCADE"), index=True, nullable=False
    )
    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    category: Mapped[str] = mapped_column(String(30), default="Weak", nullable=False)
    component_scores: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
