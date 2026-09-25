"""Structured failure analysis over system outputs."""
from __future__ import annotations

from evaluation.failures import FAILURE_STAGES, analyze_failures, summarize_failures
from evaluation.schemas import (
    EvaluationCase,
    ResearcherInput,
    SourcePaper,
    SystemGap,
    SystemHypothesis,
    SystemIntersection,
    SystemOutput,
    SystemRef,
)


def _case() -> EvaluationCase:
    return EvaluationCase(
        case_id="c1",
        label="l",
        researcher_a=ResearcherInput(name="A"),
        source_papers=[
            SourcePaper(paper_id="p1", title="Alpha paper", abstract="alpha"),
            SourcePaper(paper_id="p2", title="Beta paper", abstract="beta"),
        ],
        expected_topics=["alpha"],
        expected_evidence_references=["p1"],
    )


def _dataset(case):
    from evaluation.schemas import EvaluationDataset

    return EvaluationDataset(
        dataset_id="d", label="SYNTHETIC FIXTURE", is_synthetic=True, cases=[case]
    )


def test_clean_run_has_no_failures():
    case = _case()
    out = SystemOutput(
        system="s",
        gaps=[SystemGap(description="alpha gap", evidence_refs=[SystemRef(title="Alpha paper")])],
        intersections=[
            SystemIntersection(title="alpha bridge", description="alpha", evidence_refs=[SystemRef(title="Alpha paper")])
        ],
        hypotheses=[SystemHypothesis(text="alpha hypothesis", evidence_refs=[SystemRef(title="Alpha paper")])],
    )
    records = analyze_failures(
        _dataset(case), [{"case_id": "c1", "systems": {"s": {"status": "ok"}}}], {"c1": {"s": out}}
    )
    assert records == []


def test_error_and_empty_output_are_generation_stage():
    case = _case()
    records = analyze_failures(
        _dataset(case),
        [{"case_id": "c1", "systems": {"s": {"status": "error", "error": "boom"}, "e": {"status": "ok"}}}],
        {"c1": {"e": SystemOutput(system="e")}},
    )
    types = {r["failure_type"] for r in records}
    assert "system_error" in types and "empty_output" in types
    for r in records:
        assert r["stage"] == "generation"
        assert r["stage"] in FAILURE_STAGES


def test_untraceable_citation_and_ungrounded_hypothesis():
    case = _case()
    out = SystemOutput(
        system="s",
        gaps=[SystemGap(description="g", evidence_refs=[])],
        intersections=[
            SystemIntersection(title="t", description="d", evidence_refs=[SystemRef(title="Ghost paper")])
        ],
        hypotheses=[SystemHypothesis(text="h", evidence_refs=[SystemRef(title="Ghost paper")])],
    )
    records = analyze_failures(
        _dataset(case), [{"case_id": "c1", "systems": {"s": {"status": "ok"}}}], {"c1": {"s": out}}
    )
    by_type = {r["failure_type"]: r for r in records}
    assert by_type["untraceable_citation"]["stage"] == "grounding"
    assert "Ghost paper" in by_type["untraceable_citation"]["evidence_involved"]
    assert by_type["gap_without_evidence"]["stage"] == "retrieval"
    assert by_type["ungrounded_hypothesis"]["stage"] == "reasoning"


def test_summary_counts_by_stage_and_type():
    case = _case()
    out = SystemOutput(
        system="s",
        gaps=[SystemGap(description="g", evidence_refs=[])],
        hypotheses=[SystemHypothesis(text="h", evidence_refs=[SystemRef(title="Ghost")])],
    )
    records = analyze_failures(
        _dataset(case), [{"case_id": "c1", "systems": {"s": {"status": "ok"}}}], {"c1": {"s": out}}
    )
    summary = summarize_failures(records)
    assert summary["total"] == len(records)
    assert summary["by_system"]["s"] == len(records)
    assert sum(summary["by_stage"].values()) == len(records)
