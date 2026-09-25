"""Result aggregation for the evaluation framework."""
from __future__ import annotations

import pytest

from evaluation.human import aggregate_human_ratings
from evaluation.metrics import AUTOMATIC_METRICS, aggregate_system


def test_aggregate_system_means_and_counts():
    agg = aggregate_system(
        "kw",
        [
            {"evidence_citation_validity": 1.0, "hallucination_rate": 0.0,
             "research_gap_relevance": 0.2, "experiment_design_completeness": 0.0},
            {"evidence_citation_validity": None, "hallucination_rate": None,
             "research_gap_relevance": 0.4, "experiment_design_completeness": None},
        ],
    )
    assert agg["system"] == "kw"
    v = agg["metrics"]["evidence_citation_validity"]
    assert v["mean"] == 1.0 and v["n"] == 2 and v["min"] == 1.0 and v["max"] == 1.0
    h = agg["metrics"]["hallucination_rate"]
    assert h["mean"] == 0.0 and h["n"] == 2
    g = agg["metrics"]["research_gap_relevance"]
    assert g["mean"] == pytest.approx(0.3) and g["n"] == 2
    e = agg["metrics"]["experiment_design_completeness"]
    assert e["mean"] == 0.0 and e["n"] == 2  # None excluded from mean


def test_aggregate_system_has_only_automatic_metrics():
    agg = aggregate_system("kw", [{}])
    keys = set(agg["metrics"].keys())
    assert keys == {m["key"] for m in AUTOMATIC_METRICS}
    # human dimensions are never auto-aggregated into metric scores
    assert "relevance" not in keys
    assert "novelty" not in keys
    assert agg["human_metrics"] == {}


def test_aggregate_system_all_none_means_none():
    agg = aggregate_system(
        "sys", [{m["key"]: None for m in AUTOMATIC_METRICS}]
    )
    for key in AUTOMATIC_METRICS:
        assert agg["metrics"][key["key"]]["mean"] is None
    # every metric counts the number of cases evaluated even when value is None
    assert agg["metrics"]["evidence_citation_validity"]["n"] == 1


def test_aggregate_system_names_are_separate():
    a = aggregate_system("x", [{"evidence_citation_validity": 1.0}])
    b = aggregate_system("y", [{"evidence_citation_validity": 0.0}])
    assert a["metrics"]["evidence_citation_validity"]["mean"] == 1.0
    assert b["metrics"]["evidence_citation_validity"]["mean"] == 0.0


def test_human_aggregation_without_ratings_is_pending():
    agg = aggregate_human_ratings([])
    assert agg == {}


def test_human_aggregation_means_over_provided_ratings():
    rows = [
        {"case_id": "c1", "system": "pipeline", "intersection_index": 0,
         "relevance": 4, "novelty": 3, "plausibility": 4, "evidence_quality": 5},
        {"case_id": "c1", "system": "pipeline", "intersection_index": 1,
         "relevance": 2, "novelty": 3, "plausibility": 3, "evidence_quality": 1},
        {"case_id": "c2", "system": "keyword", "intersection_index": 0,
         "relevance": 5, "novelty": 3, "plausibility": 4, "evidence_quality": 4},
    ]
    agg = aggregate_human_ratings(rows)
    assert agg["pipeline"]["relevance"]["mean"] == 3.0
    assert agg["pipeline"]["relevance"]["n"] == 2
    assert agg["pipeline"]["novelty"]["mean"] == 3.0
    assert agg["pipeline"]["novelty"]["n"] == 2
    assert agg["keyword"]["relevance"]["mean"] == 5.0
    assert agg["keyword"]["novelty"]["n"] == 1
    # key dimensions that were never rated stay pending
    assert agg["keyword"]["evidence_quality"]["mean"] == 4.0
    missing_system = agg  # no third system rows
    assert "embedding" not in missing_system