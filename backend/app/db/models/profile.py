from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, gen_uuid, TimestampMixin


class ResearchProfile(TimestampMixin, Base):
    """A researcher's editable 'Research DNA' profile inside a workspace."""

    __tablename__ = "research_profiles"

    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False
    )
    researcher_id: Mapped[str | None] = mapped_column(
        ForeignKey("researchers.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    source_type: Mapped[str] = mapped_column(String(20), default="manual", nullable=False)
    current_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    workspace = relationship("Workspace", back_populates="profiles")
    versions = relationship(
        "ResearchProfileVersion",
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="ResearchProfileVersion.version.desc()",
    )


class ResearchProfileVersion(Base):
    """Immutable snapshot of extracted/edited Research DNA."""

    __tablename__ = "research_profile_versions"
    __table_args__ = (UniqueConstraint("profile_id", "version", name="uq_profile_version"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    profile_id: Mapped[str] = mapped_column(
        ForeignKey("research_profiles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    dna_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    profile = relationship("ResearchProfile", back_populates="versions")

