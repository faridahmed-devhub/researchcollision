"""Metric calculations for the evaluation framework."""
from __future__ import annotations

from evaluation.metrics import (
    aggregate_values,
    compute_automatic_metrics,
    evidence_citation_validity,
    evidence_grounding_precision,
    experiment_design_completeness,
    hallucination_rate,
    hypothesis_grounding_ratio,
    hypothesis_plausibility_proxy,
    intersection_relevance,
    research_gap_relevance,
    resolve_ref,
)
from evaluation.schemas import (
    EvaluationCase,
    ExpectedGap,
    SourcePaper,
    SystemGap,
    SystemHypothesis,
    SystemIntersection,
    SystemOutput,
    SystemRef,
)


def _papers():
    return [
        SourcePaper(
            paper_id="p1", title="Alpha Methods Paper", abstract="alpha methods calibration",
            topics=["alpha"], methods=["calibration"],
        ),
        SourcePaper(
            paper_id="p2", title="Beta Systems Paper", abstract="beta reader studies",
            topics=["beta"], methods=["reader study"],
        ),
        SourcePaper(
            paper_id="p3", title="Gamma Data Paper", abstract="unrelated molecule screening",
            topics=["gamma"], methods=["simulation"],
        ),
    ]


def _case() -> EvaluationCase:
    return EvaluationCase(
        case_id="c1",
        researcher_a={"name": "R A", "topics": ["alpha", "beta"], "methods": ["calibration"]},
        source_papers=[p.model_dump() for p in _papers()],
        expected_evidence_references=["p1", "p2"],
        expected_topics=["alpha", "beta"],
        expected_methods=["calibration", "reader study"],
        expected_gaps=[
            ExpectedGap(gap_id="g1", description="transfer between alpha and beta is missing")
        ],
    )


def test_resolve_ref_by_title_is_case_insensitive_and_punctuation_tolerant():
    case = _case()
    r = SystemRef(title="alpha methods paper ")
    assert resolve_ref(r, case) == "p1"


def test_resolve_ref_by_paper_id_ignores_title():
    case = _case()
    r = SystemRef(title="totally different title", paper_id="p2")
    assert resolve_ref(r, case) == "p2"


def test_resolve_ref_returns_none_for_unknown():
    assert resolve_ref(SystemRef(title="No such paper exists"), _case()) is None


def test_evidence_citation_validity_half():
    case = _case()
    out = SystemOutput(system="t")
    out.intersections = [
        SystemIntersection(
            title="i",
            description="d",
            evidence_refs=[
                SystemRef(title="Alpha Methods Paper"),
                SystemRef(title="Completely Fabricated Publication"),
            ],
        )
    ]
    assert evidence_citation_validity(out, case) == 0.5


def test_grounding_precision_and_hallucination():
    case = _case()
    out = SystemOutput(
        system="t",
        gaps=[SystemGap(description="g", evidence_refs=[
            SystemRef(title="Alpha Methods Paper"),
            SystemRef(title="Gamma Data Paper"),
            SystemRef(title="Ghost Paper"),
        ])],
    )
    # p3 is a real paper but not expected evidence; ghost is untraceable
    assert evidence_grounding_precision(out, case) == 1 / 3
    assert hallucination_rate(out, case) == 1 / 3
    assert evidence_citation_validity(out, case) == 2 / 3


def test_no_refs_means_none_for_ref_metrics():
    case = _case()
    out = SystemOutput(system="t", gaps=[SystemGap(description="g")])
    m = compute_automatic_metrics(out, case)
    assert m["evidence_citation_validity"] is None
    assert m["evidence_grounding_precision"] is None
    assert m["hallucination_rate"] is None
    assert m["citation_coverage"] == 0.0  # nothing cited of expected set


def test_citation_coverage_recall():
    case = _case()
    out = SystemOutput(
        system="t",
        intersections=[SystemIntersection(title="i", description="d", evidence_refs=[
            SystemRef(title="Alpha Methods Paper"),
        ])],
    )
    assert evidence_grounding_precision(out, case) == 1.0
    from evaluation.metrics import citation_coverage

    assert citation_coverage(out, case) == 0.5  # 1 of 2 expected refs cited
    # coverage is a fraction capped at 1.0, overshooting impossible with dedupe
    out2 = SystemOutput(
        system="t",
        intersections=[SystemIntersection(title="i", description="d", evidence_refs=[
            SystemRef(title="Alpha Methods Paper"),
            SystemRef(title="Beta Systems Paper"),
        ])],
    )
    assert citation_coverage(out2, case) == 1.0


def test_research_gap_relevance():
    case = _case()
    out = SystemOutput(system="t", gaps=[
        SystemGap(description="transfer between alpha and beta is missing from the corpus"),
    ])
    assert research_gap_relevance(out, case) > 0.9
    unrelated = SystemOutput(system="t", gaps=[
        SystemGap(description="quantum computing for agriculture"),
    ])
    assert research_gap_relevance(unrelated, case) == 0.0
    # hyphenated phrasing reduces lexical overlap (documented proxy limitation)
    hyphenated = SystemOutput(system="t", gaps=[
        SystemGap(description="alpha-beta transfer is missing from the corpus"),
    ])
    assert 0.0 < research_gap_relevance(hyphenated, case) < 0.9


def test_intersection_relevance():
    case = _case()
    out = SystemOutput(system="t", intersections=[
        SystemIntersection(title="Bridging alpha area", description="uses calibration and reader study"),
    ])
    value = intersection_relevance(out, case)
    assert value > 0.5
    empty = SystemOutput(system="t", intersections=[
        SystemIntersection(title="zzz", description="zzz"),
    ])
    assert intersection_relevance(empty, case) == 0.0


def test_hypothesis_grounding_ratio_and_plausibility():
    case = _case()
    out = SystemOutput(system="t", hypotheses=[
        SystemHypothesis(text="Application of alpha calibration yields gains",
                         evidence_refs=[SystemRef(title="Alpha Methods Paper")]),
        SystemHypothesis(text="unrelated speculation", evidence_refs=[]),
    ])
    assert hypothesis_grounding_ratio(out, case) == 0.5
    proxy = hypothesis_plausibility_proxy(out, case)
    assert 0.0 < proxy < 1.0


def test_experiment_design_completeness():
    case = _case()
    out = SystemOutput(system="t", hypotheses=[
        SystemHypothesis(text="h", experiment={
            "baseline": "standard", "dataset": "MNIST", "metrics": "dice",
        }),
    ])
    assert experiment_design_completeness(out, case) == 3 / 9
    # three hypotheses with full designs average to 1.0
    full = {
        "baseline": "b", "proposed_approach": "a", "dataset": "d",
        "training_setup": "t", "evaluation_setup": "e", "metrics": "m",
        "ablations": ["x"], "expected_outcomes": "o", "failure_conditions": "f",
    }
    out2 = SystemOutput(system="t", hypotheses=[
        SystemHypothesis(text="h1", experiment=dict(full)),
        SystemHypothesis(text="h2", experiment=dict(full)),
    ])
    assert experiment_design_completeness(out2, case) == 1.0
    no_hyp = SystemOutput(system="t")
    assert experiment_design_completeness(no_hyp, case) == 0.0


def test_llm_only_style_output_yields_none_ref_metrics():
    case = _case()
    out = SystemOutput(system="t", hypotheses=[SystemHypothesis(text="no citations")])
    m = compute_automatic_metrics(out, case)
    assert m["evidence_citation_validity"] is None
    assert m["hypothesis_grounding_ratio"] == 0.0


def test_aggregate_values():
    assert aggregate_values([1.0, 0.5]) == {"mean": 0.75, "min": 0.5, "max": 1.0, "n": 2}
    assert aggregate_values([None, None])["mean"] is None
    assert aggregate_values([])["mean"] is None
    assert aggregate_values([None, 1.0])["mean"] == 1.0