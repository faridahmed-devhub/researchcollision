from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, gen_uuid, TimestampMixin


class Setting(TimestampMixin, Base):
    """Key/value application settings (e.g., configurable ranking weights)."""

    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    value: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    user_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(60), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class AgentCall(TimestampMixin, Base):
    """Reproducibility record for every AI call (agent, prompt version, model)."""

    __tablename__ = "agent_calls"

    workspace_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    job_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    agent_name: Mapped[str] = mapped_column(String(80), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(20), default="v1", nullable=False)
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    model: Mapped[str] = mapped_column(String(200), nullable=False)
    input_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    output_schema: Mapped[str] = mapped_column(String(120), nullable=False)
    duration_ms: Mapped[float] = mapped_column(default=0.0, nullable=False)  # type: ignore[assignment]
    status: Mapped[str] = mapped_column(String(20), default="ok", nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

