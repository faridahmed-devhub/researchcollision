from __future__ import annotations

from sqlalchemy import JSON, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import AI_GENERATED_LABEL
from app.db.base import Base, TimestampMixin


class Hypothesis(TimestampMixin, Base):
    """An AI-generated research hypothesis tied to an intersection.

    Always labeled with `label` (default 'AI-GENERATED HYPOTHESIS').
    """

    __tablename__ = "hypotheses"

    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False
    )
    intersection_id: Mapped[str] = mapped_column(
        ForeignKey("research_intersections.id", ondelete="CASCADE"), index=True, nullable=False
    )
    label: Mapped[str] = mapped_column(String(60), default=AI_GENERATED_LABEL, nullable=False)
    research_question: Mapped[str] = mapped_column(Text, nullable=False)
    hypothesis_text: Mapped[str] = mapped_column(Text, nullable=False)
    motivation: Mapped[str | None] = mapped_column(Text, nullable=True)
    method: Mapped[str | None] = mapped_column(Text, nullable=True)
    dataset: Mapped[str | None] = mapped_column(Text, nullable=True)
    baseline: Mapped[str | None] = mapped_column(Text, nullable=True)
    metrics: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_contribution: Mapped[str | None] = mapped_column(Text, nullable=True)
    risks: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)

    experiment = relationship(
        "Experiment", back_populates="hypothesis", uselist=False, cascade="all, delete-orphan"
    )


class Experiment(TimestampMixin, Base):
    """Experiment design for a hypothesis. Unverified datasets are INFERRED."""

    __tablename__ = "experiments"

    hypothesis_id: Mapped[str] = mapped_column(
        ForeignKey("hypotheses.id", ondelete="CASCADE"), index=True, unique=True, nullable=False
    )
    baseline: Mapped[str | None] = mapped_column(Text, nullable=True)
    proposed_approach: Mapped[str | None] = mapped_column(Text, nullable=True)
    dataset: Mapped[str | None] = mapped_column(Text, nullable=True)
    dataset_status: Mapped[str] = mapped_column(String(20), default="INFERRED", nullable=False)
    training_setup: Mapped[str | None] = mapped_column(Text, nullable=True)
    evaluation_setup: Mapped[str | None] = mapped_column(Text, nullable=True)
    metrics: Mapped[str | None] = mapped_column(Text, nullable=True)
    ablations: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    expected_outcomes: Mapped[str | None] = mapped_column(Text, nullable=True)
    failure_conditions: Mapped[str | None] = mapped_column(Text, nullable=True)

    hypothesis = relationship("Hypothesis", back_populates="experiment")
