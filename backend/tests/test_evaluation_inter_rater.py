"""Human-rating aggregation and inter-rater reliability."""
from __future__ import annotations

import pytest

from evaluation.human import (
    _weighted_kappa,
    aggregate_human_ratings,
    inter_rater_reliability,
    make_blind_key,
)
from evaluation.schemas import SystemIntersection, SystemOutput


def _row(eid, rater, rel=None, nov=None, plaus=None, ev=None):
    return {
        "eval_id": eid, "rater": rater, "case_id": "c1", "surface": "intersection",
        "relevance": rel, "novelty": nov, "plausibility": plaus, "evidence_quality": ev,
    }


def test_weighted_kappa_perfect_ordered_agreement_is_one():
    assert _weighted_kappa([(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)]) == pytest.approx(1.0)


def test_weighted_kappa_without_variance_is_undefined():
    assert _weighted_kappa([(3, 3), (3, 3), (3, 3)]) is None


def test_weighted_kappa_partial_agreement_between_zero_and_one():
    k = _weighted_kappa([(1, 1), (2, 2), (3, 2)])
    assert k is not None and 0.0 < k < 1.0


def test_inter_rater_requires_two_raters():
    rows = [_row("EV-a", "alice", rel=4), _row("EV-b", "alice", rel=5)]
    irl = inter_rater_reliability(rows)
    assert irl["relevance"]["available"] is False
    assert irl["relevance"]["n_raters"] == 1
    assert irl["relevance"]["weighted_kappa"] is None


def test_inter_rater_two_raters_reports_kappa():
    rows = [
        _row("EV-a", "alice", rel=4), _row("EV-a", "bob", rel=4),
        _row("EV-b", "alice", rel=2), _row("EV-b", "bob", rel=3),
    ]
    irl = inter_rater_reliability(rows)
    assert irl["relevance"]["available"] is True
    assert irl["relevance"]["n_shared_items"] == 2
    assert 0.0 <= irl["relevance"]["percent_agreement"] <= 1.0
    assert irl["relevance"]["weighted_kappa"] is not None


def test_aggregate_resolves_system_through_blind_key():
    outputs = {
        "c1": {"pipeline": SystemOutput(
            system="pipeline",
            intersections=[SystemIntersection(title="IX", description="d")],
        )}
    }
    key = make_blind_key(outputs)
    (eid,) = list(key)
    rows = [_row(eid, "alice", rel=5, nov=4, plaus=3, ev=2)]
    agg = aggregate_human_ratings(rows, key)
    assert agg["pipeline"]["relevance"]["mean"] == 5.0
    assert agg["pipeline"]["evidence_quality"]["mean"] == 2.0
    assert "keyword" not in agg
