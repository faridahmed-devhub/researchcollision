from __future__ import annotations

from sqlalchemy import JSON, Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, gen_uuid, TimestampMixin


class Researcher(TimestampMixin, Base):
    """A researcher record.

    workspace_id NULL => shared reference data (seeded / global directory).
    Otherwise the researcher is scoped to a workspace.
    """

    __tablename__ = "researchers"

    workspace_id: Mapped[str | None] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=True
    )
    name: Mapped[str] = mapped_column(String(300), index=True, nullable=False)
    affiliation: Mapped[str | None] = mapped_column(String(300), nullable=True)
    homepage_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_ids: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    aliases = relationship(
        "ResearcherAlias", back_populates="researcher", cascade="all, delete-orphan"
    )
    authorships = relationship("PaperAuthor", back_populates="researcher")


class ResearcherAlias(Base):
    __tablename__ = "researcher_aliases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    researcher_id: Mapped[str] = mapped_column(
        ForeignKey("researchers.id", ondelete="CASCADE"), index=True, nullable=False
    )
    alias: Mapped[str] = mapped_column(String(300), index=True, nullable=False)

    researcher = relationship("Researcher", back_populates="aliases")

