"""Discovery job schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import DiscoveryMode


class DiscoveryJobCreate(BaseModel):
    workspace_id: str
    researcher_a_id: str
    researcher_b_id: str | None = None
    field_query: str | None = Field(default=None, description="e.g. 'Climate Science'")
    mode: DiscoveryMode = DiscoveryMode.NORMAL
    max_papers: int = Field(default=12, ge=1, le=50)
    generate_hypotheses: bool = True


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workspace_id: str
    user_id: str
    job_type: str
    status: str
    progress: float
    current_step: str | None
    total_steps: int
    error_message: str | None
    config: dict
    result_summary: dict | None
    started_at: datetime | None
    completed_at: datetime | None
    attempt: int
    created_at: datetime
    updated_at: datetime


class JobEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    event_type: str
    message: str | None
    data: dict | None
    created_at: datetime
