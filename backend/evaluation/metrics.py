"""Automatic + human metric definitions and calculations.

Automatic metrics are pure functions over (:class:`SystemOutput`,
:class:`EvaluationCase`). None of them require a live LLM. Human metrics
(relevance, novelty, plausibility, evidence quality) have rating rubrics here
but are NEVER computed automatically — they are collected by raters offline
(see ``evaluation.human``) and only reach the report if real annotations are
provided.

Terms
-----
*valid reference* — a cited reference that resolves to a paper inside the
case's source corpus or inside the system's own retrieval context
(``known_context_titles``). Untraceable / fabricated references are invalid.

*expected reference* — a paper_id listed in the dataset's
``expected_evidence_references`` (gold supporting evidence).
"""
from __future__ import annotations

import math
import re
from typing import Any

from evaluation.schemas import (
    EvaluationCase,
    SystemOutput,
    SystemRef,
)

_STOPWORDS = {
    "the", "a", "an", "of", "and", "or", "to", "in", "on", "for", "with",
    "we", "our", "is", "are", "as", "by", "at", "from", "it", "its", "be",
    "can", "has", "have", "was", "were", "which", "using", "used", "into",
    "such", "these", "this", "that", "than", "then", "over", "across",
    "between", "paper", "study", "work", "also", "how", "what", "new", "more",
    "most", "both", "each", "other", "based", "results", "show", "shows",
}

EXPERIMENT_FIELDS = [
    "baseline",
    "proposed_approach",
    "dataset",
    "training_setup",
    "evaluation_setup",
    "metrics",
    "ablations",
    "expected_outcomes",
    "failure_conditions",
]


# ---------------------------------------------------------------------------
# Metric specs (drives tables / CSV / report)
# ---------------------------------------------------------------------------

HUMAN_RATINGS = {
    "relevance": {
        "range": (1, 5),
        "definitions": {
            5: "Directly useful; squarely addresses the research gap with strong applicability",
            4: "Useful; clearly relevant with minor gaps in applicability",
            3: "Somewhat relevant; partially useful for the research gap",
            2: "Tangential; only loosely related to the researchers' work",
            1: "Irrelevant or misleading for the researchers' interests",
        },
    },
    "novelty": {
        "range": (1, 5),
        "definitions": {
            5: "Genuinely new direction not evident from existing literature",
            4: "Clearly novel framing of existing components",
            3: "Partially novel; combines known ideas in a modest new way",
            2: "Mostly familiar; little new beyond rephrasing",
            1: "Obvious or already well-covered combination",
        },
    },
    "plausibility": {
        "range": (1, 5),
        "definitions": {
            5: "Very credible; mechanisms and feasibility are strongly motivated",
            4: "Credible with reasonable assumptions",
            3: "Plausible but with notable gaps in reasoning or feasibility",
            2: "Doubtful plausibility; weak motivation or feasibility",
            1: "Implausible or internally inconsistent",
        },
    },
    "evidence_quality": {
        "range": (1, 5),
        "definitions": {
            5: "Well supported by relevant, traceable, trustworthy references",
            4: "Good support from mostly relevant references",
            3: "Some support but references are partly generic or off-target",
            2: "Weak or partly untraceable support",
            1: "No support or references are fabricated/irrelevant",
        },
    },
}

AUTOMATIC_METRICS: list[dict[str, Any]] = [
    {
        "key": "evidence_citation_validity",
        "label": "Evidence citation validity",
        "higher_is_better": True,
        "requires_human": False,
        "description": "Fraction of cited references that resolve to a real paper in the source corpus or the system's retrieval context.",
    },
    {
        "key": "evidence_grounding_precision",
        "label": "Evidence grounding precision",
        "higher_is_better": True,
        "requires_human": False,
        "requires_gold": True,
        "description": "Fraction of cited references that match the dataset's expected (gold) supporting evidence.",
    },
    {
        "key": "hallucination_rate",
        "label": "Hallucination rate",
        "higher_is_better": False,
        "requires_human": False,
        "description": "Fraction of cited references that cannot be traced to any known paper (fabricated/untraceable).",
    },
    {
        "key": "citation_coverage",
        "label": "Citation coverage (recall)",
        "higher_is_better": True,
        "requires_human": False,
        "requires_gold": True,
        "description": "Fraction of expected supporting references the system actually cited.",
    },
    {
        "key": "research_gap_relevance",
        "label": "Research-gap relevance (proxy)",
        "higher_is_better": True,
        "requires_human": True,
        "requires_gold": True,
        "description": "Automatic proxy: lexical overlap of detected gaps with the dataset's expected gaps. Human relevance rating required for final judgment.",
    },
    {
        "key": "intersection_relevance",
        "label": "Intersection relevance (proxy)",
        "higher_is_better": True,
        "requires_human": True,
        "requires_gold": True,
        "description": "Automatic proxy: lexical coverage of expected topics/methods by the discovered intersections. Human relevance/novelty ratings required for final judgment.",
    },
    {
        "key": "hypothesis_grounding_ratio",
        "label": "Hypothesis grounding ratio",
        "higher_is_better": True,
        "requires_human": False,
        "description": "Fraction of hypotheses backed by at least one valid evidence reference.",
    },
    {
        "key": "hypothesis_plausibility_proxy",
        "label": "Hypothesis plausibility (proxy)",
        "higher_is_better": True,
        "requires_human": True,
        "requires_gold": True,
        "description": "Structural proxy combining hypothesis grounding with expected-topic coverage. Human plausibility rating required for final judgment.",
    },
    {
        "key": "experiment_design_completeness",
        "label": "Experiment-design completeness",
        "higher_is_better": True,
        "requires_human": False,
        "description": "Mean fraction of standard experiment-design fields that are concretely specified.",
    },
]


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-z][a-z0-9\-]{2,}", (text or "").lower())
    return {w for w in words if w not in _STOPWORDS}


def overlap_coefficient(a: set[str], b: set[str]) -> float:
    """|A ∩ B| / min(|A|, |B|); 0 when either set is empty."""
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))


def best_overlap(phrases: list[str], targets: list[str]) -> float:
    """Max lexical overlap of any phrase in ``phrases`` with any target."""
    if not phrases or not targets:
        return 0.0
    best = 0.0
    for p in phrases:
        pt = tokenize(p)
        for t in targets:
            best = max(best, overlap_coefficient(pt, tokenize(t)))
    return best


# ---------------------------------------------------------------------------
# Reference resolution
# ---------------------------------------------------------------------------

def _norm_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", title.lower())


def resolve_ref(ref: SystemRef, case: EvaluationCase) -> str | None:
    """Resolve a reference to a dataset paper_id (or None if untraceable)."""
    paper_by_id = {p.paper_id: p for p in case.source_papers}
    if ref.paper_id and ref.paper_id in paper_by_id:
        return ref.paper_id
    n = _norm_title(ref.title)
    for p in case.source_papers:
        if _norm_title(p.title) == n:
            return p.paper_id
    return None


def output_refs_valid(refs: list[SystemRef], output: SystemOutput, case: EvaluationCase) -> list[tuple[SystemRef, bool]]:
    ctx = {_norm_title(t) for t in output.known_context_titles}
    out = []
    for r in refs:
        if resolve_ref(r, case) is not None or _norm_title(r.title) in ctx:
            out.append((r, True))
        else:
            out.append((r, False))
    return out


# ---------------------------------------------------------------------------
# Automatic metric calculations
# ---------------------------------------------------------------------------

def evidence_citation_validity(output: SystemOutput, case: EvaluationCase) -> float | None:
    refs = output.all_refs
    if not refs:
        return None
    valid = sum(1 for _, ok in output_refs_valid(refs, output, case) if ok)
    return valid / len(refs)


def evidence_grounding_precision(output: SystemOutput, case: EvaluationCase) -> float | None:
    expected = set(case.expected_evidence_references)
    if not expected:
        # No independently available gold evidence set -> not measurable (n/a),
        # never reported as 0 (which would falsely look like bad grounding).
        return None
    refs = output.all_refs
    if not refs:
        return None
    grounded = sum(
        1 for r in refs if (resolve_ref(r, case) or "") in expected
    )
    return grounded / len(refs)


def hallucination_rate(output: SystemOutput, case: EvaluationCase) -> float | None:
    refs = output.all_refs
    if not refs:
        return None
    invalid = sum(1 for _, ok in output_refs_valid(refs, output, case) if not ok)
    return invalid / len(refs)


def citation_coverage(output: SystemOutput, case: EvaluationCase) -> float | None:
    expected = set(case.expected_evidence_references)
    if not expected:
        return None
    cited = {
        resolved
        for r in output.all_refs
        if (resolved := resolve_ref(r, case)) is not None
    }
    return len(cited & expected) / len(expected)


def research_gap_relevance(output: SystemOutput, case: EvaluationCase) -> float | None:
    """Mean best lexical overlap between detected and expected gaps.

    Returns ``None`` when the dataset has no expected gaps (no independent
    annotation available) so an absent gold set is never reported as 0.0.
    """
    if not case.expected_gaps:
        return None
    if not output.gaps:
        return 0.0
    detected = [g.description for g in output.gaps]
    expected_descs = [g.description for g in case.expected_gaps]
    scores = [best_overlap([d], expected_descs) for d in detected]
    return sum(scores) / len(scores)


def intersection_relevance(output: SystemOutput, case: EvaluationCase) -> float | None:
    """Mean coverage of expected topics/methods by the discovered intersections.

    Averages only over the reference groups that are actually annotated, so a
    dataset without method labels is not penalised twice. Returns ``None`` when
    neither topics nor methods are annotated.
    """
    texts = [f"{ix.title} {ix.description}" for ix in output.intersections]
    groups: list[float] = []
    if case.expected_topics:
        groups.append(best_overlap(texts, case.expected_topics))
    if case.expected_methods:
        groups.append(best_overlap(texts, case.expected_methods))
    if not groups:
        return None
    if not output.intersections:
        return 0.0
    return sum(groups) / len(groups)


def hypothesis_grounding_ratio(output: SystemOutput, case: EvaluationCase) -> float:
    if not output.hypotheses:
        return 0.0
    grounded = sum(
        1
        for h in output.hypotheses
        if any(ok for _, ok in output_refs_valid(h.evidence_refs, output, case))
    )
    return grounded / len(output.hypotheses)


def hypothesis_plausibility_proxy(output: SystemOutput, case: EvaluationCase) -> float | None:
    """Structural proxy: 50% grounding + 50% expected-topic coverage.

    Returns ``None`` when the dataset provides neither expected evidence nor
    expected topics/methods, because there is nothing to check plausibility
    against.
    """
    expected = set(case.expected_evidence_references)
    if not (expected or case.expected_topics or case.expected_methods):
        return None
    if not output.hypotheses:
        return 0.0
    scores = []
    for h in output.hypotheses:
        grounded = 0.0
        valid = [r for r, ok in output_refs_valid(h.evidence_refs, output, case) if ok]
        if valid:
            if expected:
                grounded = sum(
                    1 for r in valid if (resolve_ref(r, case) or "") in expected
                ) / len(valid)
            else:
                # valid references exist but no gold set to match against
                grounded = 1.0
        coverage = best_overlap([h.text], case.expected_topics + case.expected_methods)
        scores.append(0.5 * grounded + 0.5 * coverage)
    return sum(scores) / len(scores)


def experiment_design_completeness(output: SystemOutput, case: EvaluationCase, fields: list[str] | None = None) -> float:
    fields = fields or EXPERIMENT_FIELDS
    if not output.hypotheses:
        return 0.0
    scores = []
    for h in output.hypotheses:
        present = sum(
            1
            for f in fields
            if str(h.experiment.get(f) or "").strip() not in ("", "None", "TBD")
        )
        scores.append(present / len(fields))
    return sum(scores) / len(scores)


def compute_automatic_metrics(output: SystemOutput, case: EvaluationCase) -> dict[str, float | None]:
    return {
        "evidence_citation_validity": evidence_citation_validity(output, case),
        "evidence_grounding_precision": evidence_grounding_precision(output, case),
        "hallucination_rate": hallucination_rate(output, case),
        "citation_coverage": citation_coverage(output, case),
        "research_gap_relevance": research_gap_relevance(output, case),
        "intersection_relevance": intersection_relevance(output, case),
        "hypothesis_grounding_ratio": hypothesis_grounding_ratio(output, case),
        "hypothesis_plausibility_proxy": hypothesis_plausibility_proxy(output, case),
        "experiment_design_completeness": experiment_design_completeness(output, case),
    }


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def aggregate_values(values: list[float]):
    """Mean/min/max over finite values; None result if none present."""
    finite = [v for v in values if v is not None and not math.isnan(v)]
    if not finite:
        return {"mean": None, "min": None, "max": None, "n": len(values)}
    return {"mean": sum(finite) / len(finite), "min": min(finite), "max": max(finite), "n": len(values)}


def aggregate_system(system_name: str, case_metrics: list[dict[str, float | None]]) -> dict[str, Any]:
    """Aggregate per-case automatic metrics for one system.

    ``case_metrics`` is one dict per case (metric key -> value, None allowed).
    Human metrics are never aggregated here; see ``evaluation.human``.
    """
    keys = [m["key"] for m in AUTOMATIC_METRICS]
    agg: dict[str, Any] = {"system": system_name, "metrics": {}, "human_metrics": {}}
    for key in keys:
        values = [cm.get(key) for cm in case_metrics]
        agg["metrics"][key] = aggregate_values(values)
    return agg