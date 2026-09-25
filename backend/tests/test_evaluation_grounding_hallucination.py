"""Evidence grounding, citation validity and hallucination semantics."""
from __future__ import annotations

from evaluation.metrics import (
    citation_coverage,
    compute_automatic_metrics,
    evidence_citation_validity,
    evidence_grounding_precision,
    hallucination_rate,
)
from evaluation.schemas import (
    EvaluationCase,
    SourcePaper,
    SystemGap,
    SystemHypothesis,
    SystemIntersection,
    SystemOutput,
    SystemRef,
)


def _case() -> EvaluationCase:
    return EvaluationCase(
        case_id="c",
        researcher_a={"name": "A"},
        source_papers=[
            SourcePaper(paper_id="p1", title="Supported Result One", abstract="x"),
            SourcePaper(paper_id="p2", title="Supported Result Two", abstract="y"),
        ],
        expected_evidence_references=["p1", "p2"],
    )


def test_all_expected_refs_grounded_is_perfect():
    case = _case()
    out = SystemOutput(
        system="t",
        hypotheses=[
            SystemHypothesis(
                text="h",
                evidence_refs=[
                    SystemRef(title="Supported Result One"),
                    SystemRef(title="Supported Result Two"),
                ],
            )
        ],
    )
    assert evidence_citation_validity(out, case) == 1.0
    assert evidence_grounding_precision(out, case) == 1.0
    assert hallucination_rate(out, case) == 0.0
    assert citation_coverage(out, case) == 1.0
    m = compute_automatic_metrics(out, case)
    assert m["hypothesis_grounding_ratio"] == 1.0


def test_fabricated_reference_flags_hallucination():
    case = _case()
    out = SystemOutput(system="t", gaps=[
        SystemGap(description="g", evidence_refs=[
            SystemRef(title="A Study That Was Never Published", paper_id="syn-999"),
        ]),
    ])
    assert evidence_citation_validity(out, case) == 0.0
    assert hallucination_rate(out, case) == 1.0
    assert evidence_grounding_precision(out, case) == 0.0


def test_retrieved_context_papers_are_valid_but_not_expected():
    """A ref retrievable by the system (its context) counts as valid, not hallucinated,
    but does not contribute to grounding precision unless it is in the expected set."""
    case = _case()
    out = SystemOutput(
        system="t",
        known_context_titles=["Supported Result One", "An Extra Retrieved Paper"],
        gaps=[SystemGap(description="g", evidence_refs=[
            SystemRef(title="An Extra Retrieved Paper"),
        ])],
    )
    assert evidence_citation_validity(out, case) == 1.0
    assert hallucination_rate(out, case) == 0.0
    # but it's not one of the gold supporting refs
    assert evidence_grounding_precision(out, case) == 0.0
    assert citation_coverage(out, case) == 0.0


def test_mixed_references_partial_grounding():
    case = _case()
    out = SystemOutput(system="t", intersections=[
        SystemIntersection(title="i", description="d", evidence_refs=[
            SystemRef(title="Supported Result One"),   # expected + valid
            SystemRef(title="Phantom Work"),           # invalid
        ]),
    ])
    assert evidence_citation_validity(out, case) == 0.5
    assert hallucination_rate(out, case) == 0.5
    assert evidence_grounding_precision(out, case) == 0.5


def test_all_refs_deduplicated_across_surfaces():
    out = SystemOutput(system="t", gaps=[
        SystemGap(description="g1", evidence_refs=[SystemRef(title="Supported Result One")]),
    ], intersections=[
        SystemIntersection(title="i", description="d",
                           evidence_refs=[SystemRef(title="Supported Result One")]),
    ], hypotheses=[
        SystemHypothesis(text="h", evidence_refs=[SystemRef(title="Supported Result One")]),
    ])
    assert len(out.all_refs) == 1


def test_expected_but_uncited_means_zero_coverage():
    case = _case()
    out = SystemOutput(system="t", hypotheses=[SystemHypothesis(text="h")])
    assert citation_coverage(out, case) == 0.0
    assert evidence_grounding_precision(out, case) is None