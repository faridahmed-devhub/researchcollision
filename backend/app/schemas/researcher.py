"""Researcher schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ResearcherCreate(BaseModel):
    name: str = Field(min_length=1, max_length=300)
    affiliation: str | None = None
    homepage_url: str | None = None
    bio: str | None = None
    aliases: list[str] = Field(default_factory=list)


class ResearcherOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workspace_id: str | None
    name: str
    affiliation: str | None
    homepage_url: str | None
    bio: str | None
    external_ids: dict
    is_synthetic: bool
    created_at: datetime


class TrajectoryPhase(BaseModel):
    period: str
    focus: str
    topics: list[str] = []
    methods: list[str] = []


class TrajectoryOut(BaseModel):
    researcher_id: str
    summary: str | None
    historical_focus: list[str] = []
    current_focus: list[str] = []
    emerging_interests: list[str] = []
    methodology_shifts: list[str] = []
    domain_shifts: list[str] = []
    topic_transitions: list[str] = []
    phases: list[TrajectoryPhase] = []
    paper_count: int = 0
