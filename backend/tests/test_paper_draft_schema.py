"""PaperDraft schema + grounding guardrails (no fabricated results/citations)."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.agents.paper_writer_agent import PaperWriterAgent
from app.providers.llm.base import PaperDraft
from app.schemas.paper_draft import EXPECTED_RESULTS_LABEL

VALID = dict(
    title="Grounded Research Proposal",
    abstract="An abstract.",
    introduction="An introduction.",
    related_work="Related work.",
    research_gap="A gap.",
    research_question="Q?",
    hypothesis="H.",
    methodology="M.",
    experiment_design="E.",
    expected_results="Expected outcomes.",
    limitations=["lim 1"],
    conclusion="C.",
    evidence_ids=["ev-1"],
    citation_evidence_ids=["ev-1"],
)


def test_draft_has_no_actual_results_field():
    assert "actual_results" not in PaperDraft.model_fields, (
        "a paper draft must never carry actual empirical results"
    )


def test_draft_accepts_valid_minimum():
    draft = PaperDraft(**VALID)
    assert draft.title == "Grounded Research Proposal"
    assert draft.evidence_ids == ["ev-1"]


def test_fixed_labels_cannot_be_overridden():
    draft = PaperDraft(**{**VALID, "expected_results_label": "FABRICATED RESULTS"})
    assert draft.expected_results_label == EXPECTED_RESULTS_LABEL


def test_duplicate_evidence_ids_deduped():
    draft = PaperDraft(**{**VALID, "evidence_ids": ["a", "a", "b"], "citation_evidence_ids": ["b", "b"]})
    assert draft.evidence_ids == ["a", "b"]
    assert draft.citation_evidence_ids == ["b"]


def test_empty_evidence_lists_allowed():
    draft = PaperDraft(**{**VALID, "evidence_ids": [], "citation_evidence_ids": []})
    assert draft.evidence_ids == []


def test_missing_required_fields_rejected():
    required = [k for k in PaperDraft.model_fields.keys() if not k.startswith("expected") and k not in ("draft_status", "evidence_ids", "citation_evidence_ids", "limitations")]
    assert required, "expected mandatory fields to exist"
    for field in ("title", "abstract", "research_question", "conclusion"):
        bad = {k: v for k, v in VALID.items() if k != field}
        with pytest.raises(ValidationError):
            PaperDraft(**bad)


def test_paper_writer_finalize_clamps_invented_ids():
    agent = PaperWriterAgent(None)  # type: ignore[arg-type]  # finalize does not touch the LLM
    draft = PaperDraft(**{**VALID, "evidence_ids": ["ev-1", "invented-ev", "ev-2"]})
    out = agent.finalize(draft, allowed_evidence_ids=["ev-1"])
    assert out.evidence_ids == ["ev-1"]
    assert out.citation_evidence_ids == ["ev-1"]


def test_paper_writer_finalize_empty_allowed_set_empties_grounding():
    agent = PaperWriterAgent(None)  # type: ignore[arg-type]
    draft = PaperDraft(**{**VALID, "evidence_ids": ["ev-1"]})
    out = agent.finalize(draft, allowed_evidence_ids=[])
    assert out.evidence_ids == []
    assert out.citation_evidence_ids == []