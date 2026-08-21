from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import DiscoveryMode
from app.db.base import Base, TimestampMixin


class Workspace(TimestampMixin, Base):
    __tablename__ = "workspaces"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    discovery_mode: Mapped[str] = mapped_column(
        String(20), default=DiscoveryMode.NORMAL.value, nullable=False
    )

    user = relationship("User", back_populates="workspaces")
    profiles = relationship(
        "ResearchProfile", back_populates="workspace", cascade="all, delete-orphan"
    )
    jobs = relationship(
        "ResearchJob", back_populates="workspace", cascade="all, delete-orphan"
    )
    reports = relationship(
        "GeneratedReport", back_populates="workspace", cascade="all, delete-orphan"
    )
