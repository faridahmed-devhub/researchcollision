"""Structured failure analysis for evaluation runs.

Every *serious* failure observed in a run is recorded with a stable schema so
it can be audited and reproduced:

    {
      "case_id": ..., "evaluation_question": ...,
      "system": ..., "failure_type": ..., "stage": ...,
      "evidence_involved": [titles/ids...],
      "output_excerpt": ..., "detail": ...
    }

``stage`` is one of ``retrieval | grounding | reasoning | generation`` and
classifies *where* the failure originated:

* **retrieval**  — the system produced a claim with no evidence attached.
* **grounding**  — the system cited evidence that is untraceable / unsupported.
* **reasoning**  — the claim is grounded but structurally unsupported (e.g. a
  hypothesis that references nothing usable).
* **generation** — the run crashed or produced no output at all.

Nothing is invented: a clean run yields an empty list, and every record is
derived from the actual system output or error.
"""
from __future__ import annotations

from typing import Any

from evaluation.metrics import output_refs_valid
from evaluation.schemas import EvaluationCase, SystemOutput

FAILURE_STAGES = ("retrieval", "grounding", "reasoning", "generation")

_MAX_EXCERPT = 240


def _excerpt(text: str) -> str:
    text = (text or "").strip().replace("\n", " ")
    return text if len(text) <= _MAX_EXCERPT else text[: _MAX_EXCERPT - 3] + "..."


def _record(
    *,
    case: EvaluationCase,
    system: str,
    failure_type: str,
    stage: str,
    evidence_involved: list[str],
    output_excerpt: str,
    detail: str,
) -> dict[str, Any]:
    assert stage in FAILURE_STAGES, stage
    return {
        "case_id": case.case_id,
        "evaluation_question": case.evaluation_question,
        "system": system,
        "failure_type": failure_type,
        "stage": stage,
        "evidence_involved": evidence_involved,
        "output_excerpt": output_excerpt,
        "detail": detail,
    }


def _surface_label(surface: str, index: int) -> str:
    return f"{surface}[{index}]"


def analyze_failures(
    dataset,
    case_results: list[dict[str, Any]],
    outputs_by_case: dict[str, dict[str, SystemOutput]],
) -> list[dict[str, Any]]:
    cases = {c.case_id: c for c in dataset.cases}
    records: list[dict[str, Any]] = []

    for case_result in case_results:
        case_id = case_result["case_id"]
        case = cases.get(case_id)
        if case is None:
            continue
        for system_name, run in case_result["systems"].items():
            if run.get("status") != "ok":
                records.append(_record(
                    case=case, system=system_name,
                    failure_type="system_error", stage="generation",
                    evidence_involved=[], output_excerpt="",
                    detail=f"run raised: {run.get('error') or 'unknown error'}",
                ))
                continue
            output = outputs_by_case.get(case_id, {}).get(system_name)
            if output is None:
                continue
            records.extend(_analyze_output(case, system_name, output))

    records.sort(key=lambda r: (r["case_id"], r["system"], r["stage"], r["failure_type"]))
    return records


def _analyze_output(case: EvaluationCase, system: str, output: SystemOutput) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    if not (output.gaps or output.intersections or output.hypotheses):
        records.append(_record(
            case=case, system=system,
            failure_type="empty_output", stage="generation",
            evidence_involved=[], output_excerpt="",
            detail="system produced no gaps, intersections, or hypotheses",
        ))
        return records

    # --- grounding: untraceable citations anywhere in the output -----------
    invalid_titles: list[str] = []
    for ref, ok in output_refs_valid(output.all_refs, output, case):
        if not ok:
            invalid_titles.append(ref.paper_id or ref.title)
    if invalid_titles:
        records.append(_record(
            case=case, system=system,
            failure_type="untraceable_citation", stage="grounding",
            evidence_involved=sorted(set(invalid_titles)),
            output_excerpt=_excerpt("; ".join(sorted(set(invalid_titles)))),
            detail=(
                f"{len(set(invalid_titles))} cited reference(s) could not be resolved to "
                "the case corpus or the system's own retrieval context (fabricated/untraceable)"
            ),
        ))

    # --- retrieval/grounding: surfaces with no evidence --------------------
    for i, g in enumerate(output.gaps):
        if not g.evidence_refs:
            records.append(_record(
                case=case, system=system,
                failure_type="gap_without_evidence", stage="retrieval",
                evidence_involved=[], output_excerpt=_excerpt(g.description),
                detail=f"gap {_surface_label('gap', i)} is asserted without any evidence reference",
            ))
    for i, ix in enumerate(output.intersections):
        if not ix.evidence_refs:
            records.append(_record(
                case=case, system=system,
                failure_type="intersection_without_evidence", stage="retrieval",
                evidence_involved=[], output_excerpt=_excerpt(ix.title or ix.description),
                detail=(
                    f"intersection {_surface_label('intersection', i)} cites no evidence, "
                    "so its direction cannot be traced to the literature"
                ),
            ))

    # --- reasoning: hypotheses without usable grounding --------------------
    for i, h in enumerate(output.hypotheses):
        valid = [r for r, ok in output_refs_valid(h.evidence_refs, output, case) if ok]
        if not valid:
            records.append(_record(
                case=case, system=system,
                failure_type="ungrounded_hypothesis", stage="reasoning",
                evidence_involved=[r.title for r in h.evidence_refs],
                output_excerpt=_excerpt(h.text),
                detail=(
                    f"hypothesis {_surface_label('hypothesis', i)} is not backed by any "
                    "traceable evidence reference"
                ),
            ))

    # --- reasoning: expected topics entirely uncovered ---------------------
    if case.expected_topics:
        from evaluation.metrics import best_overlap

        texts = [f"{ix.title} {ix.description}" for ix in output.intersections]
        if texts and best_overlap(texts, case.expected_topics) == 0.0:
            records.append(_record(
                case=case, system=system,
                failure_type="no_expected_topic_covered", stage="reasoning",
                evidence_involved=[],
                output_excerpt=_excerpt(" | ".join(texts)[:200]),
                detail=(
                    "no discovered intersection lexically covers any expected topic of "
                    "this case (possible sparse or off-target reasoning)"
                ),
            ))

    return records


def summarize_failures(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_stage: dict[str, int] = {}
    by_type: dict[str, int] = {}
    by_system: dict[str, int] = {}
    for r in records:
        by_stage[r["stage"]] = by_stage.get(r["stage"], 0) + 1
        by_type[r["failure_type"]] = by_type.get(r["failure_type"], 0) + 1
        by_system[r["system"]] = by_system.get(r["system"], 0) + 1
    return {
        "total": len(records),
        "by_stage": by_stage,
        "by_type": by_type,
        "by_system": by_system,
    }
