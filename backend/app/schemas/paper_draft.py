"""Research-paper draft schemas.

A paper draft is an AI-generated *research proposal* grounded in stored
workspace evidence. It never reports experimental results: every factual
claim must trace to stored evidence/papers, and anything not yet measured
is explicitly labeled EXPECTED / PROPOSED.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

# Fixed guardrail label rendered above the expected-results section.
EXPECTED_RESULTS_LABEL = "EXPECTED / PROPOSED OUTCOMES — NOT EMPIRICALLY VALIDATED"

# Fixed label applied to the whole document.
DRAFT_STATUS_LABEL = (
    "AI-GENERATED RESEARCH-PAPER DRAFT — PROPOSED RESEARCH, NOT VALIDATED FINDINGS"
)


class PaperCitation(BaseModel):
    """A footnote-style reference resolved by the backend from stored evidence.

    The reference text is built server-side from the linked stored paper
    (title/venue/year/authors), so the model can never fabricate citations.
    """

    evidence_id: str
    number: int
    status: str
    text: str


class PaperEvidenceRef(BaseModel):
    """Grounding item: stored evidence referenced by the draft."""

    evidence_id: str
    claim: str
    status: str
    source_title: str | None = None
    source_url: str | None = None


class PaperDraft(BaseModel):
    """Structured research-paper draft (what the LLM produces)."""

    title: str = Field(min_length=1, max_length=400)
    abstract: str
    introduction: str
    related_work: str
    research_gap: str
    research_question: str
    hypothesis: str
    methodology: str
    experiment_design: str
    expected_results: str
    limitations: list[str] = Field(default_factory=list)
    conclusion: str
    evidence_ids: list[str] = Field(default_factory=list)
    citation_evidence_ids: list[str] = Field(default_factory=list)

    # Labels are fixed by the system, never produced by the model.
    expected_results_label: str = EXPECTED_RESULTS_LABEL
    draft_status: str = DRAFT_STATUS_LABEL

    @field_validator("evidence_ids", "citation_evidence_ids")
    @classmethod
    def _no_duplicate_ids(cls, v: list[str]) -> list[str]:
        return list(dict.fromkeys(v or []))

    @field_validator("expected_results_label", "draft_status", mode="before")
    @classmethod
    def _force_fixed_labels(cls, v, info) -> str:  # noqa: ANN001
        """Labels are system-controlled; the model can never change them."""
        if info.field_name == "expected_results_label":
            return EXPECTED_RESULTS_LABEL
        return DRAFT_STATUS_LABEL


class PaperDraftCreate(BaseModel):
    """Request payload for regenerating a paper draft for a job (reserved)."""

    regenerate: bool = True


class PaperDraftOut(BaseModel):
    """Complete draft returned to the client."""

    report_id: str
    job_id: str
    workspace_id: str
    title: str
    abstract: str
    introduction: str
    related_work: str
    research_gap: str
    research_question: str
    hypothesis: str
    methodology: str
    experiment_design: str
    expected_results: str
    expected_results_label: str
    limitations: list[str]
    conclusion: str
    evidence: list[PaperEvidenceRef]
    citations: list[PaperCitation]
    draft_status: str
    created_at: datetime

    @classmethod
    def from_draft(
        cls,
        *,
        report_id: str,
        job_id: str,
        workspace_id: str,
        draft: PaperDraft,
        evidence: list[PaperEvidenceRef],
        citations: list[PaperCitation],
        created_at: datetime,
    ) -> "PaperDraftOut":
        return cls(
            report_id=report_id,
            job_id=job_id,
            workspace_id=workspace_id,
            title=draft.title,
            abstract=draft.abstract,
            introduction=draft.introduction,
            related_work=draft.related_work,
            research_gap=draft.research_gap,
            research_question=draft.research_question,
            hypothesis=draft.hypothesis,
            methodology=draft.methodology,
            experiment_design=draft.experiment_design,
            expected_results=draft.expected_results,
            expected_results_label=draft.expected_results_label,
            limitations=draft.limitations,
            conclusion=draft.conclusion,
            evidence=evidence,
            citations=citations,
            draft_status=draft.draft_status,
            created_at=created_at,
        )