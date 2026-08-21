"""Ranking Agent — transparent weighted collaboration scoring."""
from __future__ import annotations

import structlog

from app.core.constants import (
    DEFAULT_COLLABORATION_WEIGHTS,
    CollaborationCategory,
)

logger = structlog.get_logger(__name__)


def category_for_score(score: float) -> str:
    if score >= 90:
        return CollaborationCategory.EXCEPTIONAL.value
    if score >= 80:
        return CollaborationCategory.STRONG.value
    if score >= 70:
        return CollaborationCategory.PROMISING.value
    if score >= 60:
        return CollaborationCategory.EXPLORATORY.value
    return CollaborationCategory.WEAK.value


class RankingAgent:
    name = "ranking_agent"

    def rank_pair(
        self,
        *,
        weights: dict[str, float] | None = None,
        research_relevance: float,
        method_complementarity: float,
        trajectory_alignment: float,
        gap_relevance: float,
        evidence_strength: float,
        feasibility: float,
    ) -> dict:
        w = {**DEFAULT_COLLABORATION_WEIGHTS, **(weights or {})}
        components = {
            "research_relevance": max(0.0, min(1.0, research_relevance)),
            "method_complementarity": max(0.0, min(1.0, method_complementarity)),
            "trajectory_alignment": max(0.0, min(1.0, trajectory_alignment)),
            "gap_relevance": max(0.0, min(1.0, gap_relevance)),
            "evidence_strength": max(0.0, min(1.0, evidence_strength)),
            "feasibility": max(0.0, min(1.0, feasibility)),
        }
        total = sum(components[k] * w.get(k, 0.0) for k in components)
        score = round(total * 100, 1)
        return {
            "score": score,
            "category": category_for_score(score),
            "component_scores": {k: round(v, 3) for k, v in components.items()},
            "weights_used": w,
        }

    def score_components_from_context(
        self,
        *,
        shared_topics: list[str],
        a_methods: list[str],
        b_methods: list[str],
        intersection_novelty: float,
        intersection_feasibility: float,
        evidence_count: int,
        verified_ratio: float,
        gap_confidence: float,
    ) -> dict:
        """Derive component scores from pipeline context (deterministic)."""
        relevance = min(1.0, len(shared_topics) / 3.0 * 0.6 + intersection_feasibility * 0.4)
        complementarity = 0.0
        if a_methods and b_methods:
            overlap = len(set(a_methods) & set(b_methods)) / max(len(set(a_methods) | set(b_methods)), 1)
            complementarity = 1.0 - overlap  # complementary == different methods
        alignment = (intersection_feasibility + intersection_novelty) / 2.0
        gap_rel = gap_confidence
        ev_strength = min(1.0, (evidence_count / 6.0) * 0.7 + verified_ratio * 0.3)
        return {
            "research_relevance": relevance,
            "method_complementarity": complementarity,
            "trajectory_alignment": alignment,
            "gap_relevance": gap_rel,
            "evidence_strength": ev_strength,
            "feasibility": intersection_feasibility,
        }
