"""Regression tests: collaboration weight keys must match the ranking engine."""
from __future__ import annotations

from app.agents.ranking_agent import RankingAgent
from app.core.constants import DEFAULT_COLLABORATION_WEIGHTS

REQUIRED_KEYS = {
    "research_relevance",
    "method_complementarity",
    "trajectory_alignment",
    "gap_relevance",
    "evidence_strength",
    "feasibility",
}


def test_default_weight_keys_match_ranking_components():
    assert set(DEFAULT_COLLABORATION_WEIGHTS) == REQUIRED_KEYS


def test_default_weights_sum_to_one():
    assert abs(sum(DEFAULT_COLLABORATION_WEIGHTS.values()) - 1.0) < 1e-6


def test_component_scores_use_exact_same_keys():
    comps = RankingAgent().score_components_from_context(
        shared_topics=["a", "b"],
        a_methods=["x", "y"],
        b_methods=["z"],
        intersection_novelty=0.7,
        intersection_feasibility=0.6,
        evidence_count=3,
        verified_ratio=0.5,
        gap_confidence=0.8,
    )
    assert set(comps) == REQUIRED_KEYS


def test_each_weight_actually_changes_score():
    """Every weighted slider must influence the final collaboration score."""
    comps = {
        "research_relevance": 0.8,
        "method_complementarity": 0.4,
        "trajectory_alignment": 0.6,
        "gap_relevance": 0.7,
        "evidence_strength": 0.5,
        "feasibility": 0.3,
    }
    agent = RankingAgent()
    base = agent.rank_pair(**comps)["score"]
    for key in DEFAULT_COLLABORATION_WEIGHTS:
        boosted = agent.rank_pair(weights={key: 1.0}, **comps)["score"]
        assert boosted != base, f"weight {key} has no effect on score"


def test_settings_service_ignores_unknown_keys(db_session):
    from app.services.settings_service import SettingsService

    svc = SettingsService(db_session)
    # legacy/unknown frontend keys (topic_overlap etc.) must be dropped
    svc.set(
        "collaboration_weights",
        {"topic_overlap": 0.9, "career_stage_alignment": 0.8, "trajectory_momentum": 0.7},
    )
    assert svc.collaboration_weights() == DEFAULT_COLLABORATION_WEIGHTS


async def test_settings_update_applies_known_key(auth, client):
    ws = await auth.create_workspace()
    r = await client.put(
        f"/api/v1/workspaces/{ws['id']}/settings",
        json={"collaboration_weights": {"research_relevance": 0.4}},
        headers=auth.headers,
    )
    assert r.status_code == 200
    weights = r.json()["collaboration_weights"]
    assert weights["research_relevance"] == 0.4