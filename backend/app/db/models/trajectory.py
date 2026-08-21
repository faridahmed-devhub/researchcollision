from __future__ import annotations

from sqlalchemy import JSON, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class ResearchTrajectory(TimestampMixin, Base):
    """Chronological research trajectory for a researcher within a workspace."""

    __tablename__ = "research_trajectories"
    __table_args__ = (
        UniqueConstraint("workspace_id", "researcher_id", name="uq_traj_ws_researcher"),
    )

    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False
    )
    researcher_id: Mapped[str] = mapped_column(
        ForeignKey("researchers.id", ondelete="CASCADE"), index=True, nullable=False
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    trajectory_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
