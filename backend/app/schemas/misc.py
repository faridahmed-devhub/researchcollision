"""Paper + report + stats schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PaperOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    doi: str | None
    title: str
    abstract: str | None
    publication_year: int | None
    venue: str | None
    source_provider: str
    provider_id: str
    source_url: str | None
    citation_count: int
    is_synthetic: bool
    created_at: datetime


class PaperAnalysisOut(BaseModel):
    paper_id: str
    research_problem: str | None = None
    research_question: str | None = None
    methodology: str | None = None
    dataset: str | None = None
    main_result: str | None = None
    limitations: list[str] = []
    future_work: list[str] = []
    domain: str | None = None
    methods: list[str] = []
    technologies: list[str] = []


class ReportCreate(BaseModel):
    workspace_id: str
    job_id: str | None = None
    format: str = "markdown"
    title: str | None = None


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workspace_id: str
    job_id: str | None
    title: str
    format: str
    content: str
    meta: dict | None
    created_at: datetime


class WorkspaceStats(BaseModel):
    papers_analyzed: int = 0
    researchers_analyzed: int = 0
    gaps: int = 0
    intersections: int = 0
    hypotheses: int = 0
    collaboration_opportunities: int = 0
    avg_confidence: float = 0.0
    active_jobs: int = 0
    topics: list[dict] = []
    timeline: list[dict] = []
    methods: list[dict] = []
    domains: list[dict] = []
    opportunity_scores: list[dict] = []


class ProviderStatus(BaseModel):
    llm_provider: str
    llm_model: str
    mock_mode: bool
    embedding_provider: str
    literature_provider: str
    app_env: str
