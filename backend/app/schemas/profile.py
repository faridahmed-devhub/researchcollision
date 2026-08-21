"""Research profile (Research DNA) schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ResearchDNA(BaseModel):
    """The canonical Research DNA structure (spec §13)."""

    domains: list[str] = Field(default_factory=list)
    research_problems: list[str] = Field(default_factory=list)
    methods: list[str] = Field(default_factory=list)
    datasets: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    research_questions: list[str] = Field(default_factory=list)
    publications: list[str] = Field(default_factory=list)
    technical_skills: list[str] = Field(default_factory=list)
    research_interests: list[str] = Field(default_factory=list)
    emerging_interests: list[str] = Field(default_factory=list)
    experience: list[str] = Field(default_factory=list)

    def merged(self, other: "ResearchDNA") -> "ResearchDNA":
        data = self.model_dump()
        for key, values in other.model_dump().items():
            existing = set(data.get(key) or [])
            data[key] = [*(data.get(key) or []), *[v for v in values if v not in existing]]
        return ResearchDNA(**data)


class ProfileCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    dna: dict[str, Any] = Field(default_factory=dict)


class ProfileUpdate(BaseModel):
    name: str | None = None
    dna: dict[str, Any] | None = None


class ProfileVersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    version: int
    dna_json: dict
    created_at: datetime


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workspace_id: str
    researcher_id: str | None
    name: str
    source_type: str
    current_version: int
    created_at: datetime
    updated_at: datetime


class ProfileDetailOut(ProfileOut):
    dna: dict
    versions: list[ProfileVersionOut] = []
