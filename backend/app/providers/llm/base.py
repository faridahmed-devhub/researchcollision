"""LLM provider interface + agent output schemas (AI output validation)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field


@dataclass
class LLMResponse:
    content: str
    model: str
    provider: str
    usage: dict = field(default_factory=dict)


@runtime_checkable
class LLMProvider(Protocol):
    """Every LLM backend implements this interface."""

    name: str
    model: str

    async def generate(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.2,
        max_tokens: int = 2000,
    ) -> LLMResponse: ...

    async def structured_generate(
        self,
        *,
        task: str,
        input_data: dict[str, Any],
        schema_name: str,
        schema: dict[str, Any],
        temperature: float = 0.2,
    ) -> dict[str, Any]: ...


# ---------------------------------------------------------------------------
# Agent output schemas — every AI output is validated against these (§53).
# ---------------------------------------------------------------------------


class PaperAnalysis(BaseModel):
    research_problem: str = ""
    research_question: str | None = None
    methodology: str | None = None
    dataset: str | None = None
    main_result: str | None = None
    limitations: list[str] = Field(default_factory=list)
    future_work: list[str] = Field(default_factory=list)
    domain: str | None = None
    methods: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)


class TrajectoryPhase(BaseModel):
    period: str
    focus: str
    topics: list[str] = []
    methods: list[str] = []


class TrajectoryAnalysis(BaseModel):
    historical_focus: list[str] = []
    current_focus: list[str] = []
    emerging_interests: list[str] = []
    methodology_shifts: list[str] = []
    domain_shifts: list[str] = []
    topic_transitions: list[str] = []
    phases: list[TrajectoryPhase] = []
    summary: str = ""
    evidence_ids: list[str] = []


class GapCandidate(BaseModel):
    description: str
    gap_type: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_ids: list[str] = []


class GapDetectionResult(BaseModel):
    gaps: list[GapCandidate]


class IntersectionCandidate(BaseModel):
    title: str
    description: str
    shared_problem: str
    complementary_expertise: str
    research_gap: str
    why_researcher_a: str
    why_researcher_b: str
    novelty_confidence: float = Field(ge=0.0, le=1.0)
    feasibility_confidence: float = Field(ge=0.0, le=1.0)
    evidence_ids: list[str] = []
    gap_index: int | None = None


class IntersectionResult(BaseModel):
    intersections: list[IntersectionCandidate]


class HypothesisDraft(BaseModel):
    research_question: str
    hypothesis: str
    motivation: str
    method: str
    dataset: str
    baseline: str
    metrics: str
    expected_contribution: str
    risks: str
    evidence_ids: list[str] = []


class ExperimentDraft(BaseModel):
    baseline: str
    proposed_approach: str
    dataset: str
    dataset_status: str = "INFERRED"
    training_setup: str
    evaluation_setup: str
    metrics: str
    ablations: list[str] = []
    expected_outcomes: str
    failure_conditions: str


AGENT_SCHEMAS: dict[str, dict[str, Any]] = {
    "PaperAnalysis": PaperAnalysis.model_json_schema(),
    "TrajectoryAnalysis": TrajectoryAnalysis.model_json_schema(),
    "GapDetectionResult": GapDetectionResult.model_json_schema(),
    "IntersectionResult": IntersectionResult.model_json_schema(),
    "HypothesisDraft": HypothesisDraft.model_json_schema(),
    "ExperimentDraft": ExperimentDraft.model_json_schema(),
}
