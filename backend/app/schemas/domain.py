"""Intersection / gap / hypothesis / collaboration / evidence schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EvidenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    claim: str
    source_url: str | None
    source_type: str
    paper_id: str | None
    source_title: str | None
    evidence_text: str | None
    confidence: float
    status: str
    retrieved_at: datetime | None
    created_at: datetime


class GapOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workspace_id: str
    description: str
    gap_type: str
    confidence: float
    status: str
    created_at: datetime


class GapDetailOut(GapOut):
    evidence: list[EvidenceOut] = []


class ResearcherRef(BaseModel):
    id: str
    name: str
    affiliation: str | None = None


class IntersectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workspace_id: str
    job_id: str | None
    title: str
    description: str
    shared_problem: str | None
    complementary_expertise: str | None
    research_gap_id: str | None
    gap_description: str | None
    researcher_a_id: str
    researcher_b_id: str
    why_researcher_a: str | None
    why_researcher_b: str | None
    novelty_confidence: float
    feasibility_confidence: float
    discovery_mode: str
    status: str
    created_at: datetime


class IntersectionDetailOut(IntersectionOut):
    researcher_a: ResearcherRef | None = None
    researcher_b: ResearcherRef | None = None
    evidence: list[EvidenceOut] = []
    hypotheses: list["HypothesisOut"] = []


class HypothesisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workspace_id: str
    intersection_id: str
    label: str
    research_question: str
    hypothesis_text: str
    motivation: str | None
    method: str | None
    dataset: str | None
    baseline: str | None
    metrics: str | None
    expected_contribution: str | None
    risks: str | None
    confidence: float
    created_at: datetime


class ExperimentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    hypothesis_id: str
    baseline: str | None
    proposed_approach: str | None
    dataset: str | None
    dataset_status: str
    training_setup: str | None
    evaluation_setup: str | None
    metrics: str | None
    ablations: list
    expected_outcomes: str | None
    failure_conditions: str | None


class HypothesisDetailOut(HypothesisOut):
    experiment: ExperimentOut | None = None
    intersection: IntersectionOut | None = None
    evidence: list[EvidenceOut] = []


class CollaborationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workspace_id: str
    intersection_id: str | None
    researcher_a_id: str
    researcher_b_id: str
    score: float
    category: str
    component_scores: dict
    rationale: str | None
    created_at: datetime


IntersectionDetailOut.model_rebuild()
