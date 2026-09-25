"""PaperWriterAgent: grounded, deterministic draft generation under mock LLM."""
from __future__ import annotations

from app.agents.paper_writer_agent import PaperWriterAgent
from app.schemas.paper_draft import EXPECTED_RESULTS_LABEL

CONTEXT = {
    "intersection": {
        "title": "Neural Interfaces for Climate Modeling",
        "description": "Combining neuro-symbolic methods with climate science.",
        "gap_description": "No existing work combines these two streams.",
        "complementary_expertise": "ML + Earth systems",
        "researcher_a_name": "Dr. A",
        "researcher_b_name": "Dr. B",
    },
    "hypothesis": {
        "research_question": "Can neuro-symbolic models improve climate downscaling?",
        "hypothesis_text": "A hybrid method outperforms baselines.",
        "motivation": "Informed by stored evidence.",
        "method": "Hybrid neuro-symbolic pipeline",
        "dataset": "CMIP6 (INFERRED)",
        "baseline": "U-Net (INFERRED)",
        "metrics": "RMSE",
    },
    "experiment": {
        "proposed_approach": "Train hybrid model on CMIP6.",
        "dataset": "CMIP6",
        "dataset_status": "INFERRED",
        "evaluation_setup": "LOGO cross validation.",
        "ablations": ["drop symbolic component"],
        "failure_conditions": "No improvement",
    },
    "evidence": [
        {"id": "ev-1", "claim": "Claim one.", "status": "VERIFIED", "source_title": "Paper One"},
        {"id": "ev-2", "claim": "Claim two.", "status": "INFERRED", "source_title": "Paper Two"},
    ],
}


async def test_generate_draft_is_grounded_in_supplied_evidence(mock_llm):
    agent = PaperWriterAgent(mock_llm)
    draft = await agent.generate_draft(CONTEXT)
    allowed = {e["id"] for e in CONTEXT["evidence"]}
    assert draft.title == "Neural Interfaces for Climate Modeling"
    assert set(draft.evidence_ids) <= allowed, "draft must only cite supplied evidence"
    assert set(draft.citation_evidence_ids) <= allowed
    assert draft.evidence_ids, "draft should reference some evidence"
    assert "EXPECTED / PROPOSED" in draft.expected_results, (
        "expected results must be framed as expectations, never facts"
    )
    assert "no experimental results have been collected" in draft.expected_results.lower()
    assert draft.expected_results_label == EXPECTED_RESULTS_LABEL
    assert draft.draft_status.startswith("AI-GENERATED")


async def test_generate_draft_without_hypothesis_or_evidence_still_grounded(mock_llm):
    agent = PaperWriterAgent(mock_llm)
    draft = await agent.generate_draft(
        {"intersection": {"title": "T", "description": "D"}, "hypothesis": {}, "experiment": {}, "evidence": []}
    )
    assert draft.title == "T"
    assert draft.evidence_ids == []
    assert draft.citation_evidence_ids == []
    assert "no experimental results" in draft.expected_results.lower()


def test_agent_schema_registration():
    from app.providers.llm.base import AGENT_SCHEMAS

    assert "PaperDraft" in AGENT_SCHEMAS
    schema = AGENT_SCHEMAS["PaperDraft"]
    props = schema["properties"]
    for field in (
        "title", "abstract", "introduction", "related_work", "research_gap",
        "research_question", "hypothesis", "methodology", "experiment_design",
        "expected_results", "limitations", "conclusion", "evidence_ids",
        "citation_evidence_ids",
    ):
        assert field in props, f"PaperDraft schema missing {field}"
    assert "actual_results" not in props