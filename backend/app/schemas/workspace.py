"""Workspace schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    discovery_mode: str = "normal"


class WorkspaceUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    discovery_mode: str | None = None


class WorkspaceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    discovery_mode: str
    created_at: datetime
    updated_at: datetime
