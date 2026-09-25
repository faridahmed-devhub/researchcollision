"""Reproducible evaluation runner.

Loads a dataset, runs the selected systems/baselines over each case, computes
automatic metrics, aggregates them per system, exports JSON + CSV results, a
blind human-rating template, and (optionally) merges existing human
annotations when provided.

The runner never fabricates human scores: if no rating file is supplied the
human-metrics section of every artifact states they are *pending
annotation*.
"""
from __future__ import annotations

import asyncio
import csv
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evaluation.baselines import DEFAULT_SYSTEMS, get_system
from evaluation.environment import configure_offline_defaults
from evaluation.failures import analyze_failures, summarize_failures
from evaluation.human import (
    aggregate_human_ratings,
    export_human_template,
    inter_rater_reliability,
    load_human_ratings,
    make_blind_key,
)
from evaluation.metrics import (
    AUTOMATIC_METRICS,
    HUMAN_RATINGS,
    aggregate_system,
    compute_automatic_metrics,
)
from evaluation.schemas import EvaluationDataset

configure_offline_defaults()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class CaseSystemRun:
    status: str = "ok"  # ok | error
    error: str | None = None
    metrics: dict[str, float | None] = field(default_factory=dict)
    output: Any | None = None
    duration_ms: float = 0.0


def load_dataset(path: str | Path) -> EvaluationDataset:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return EvaluationDataset.model_validate(data)


def dataset_stats(ds: EvaluationDataset) -> list[dict[str, Any]]:
    stats = []
    for case in ds.cases:
        stats.append(
            {
                "case_id": case.case_id,
                "label": case.label,
                "n_source_papers": len(case.source_papers),
                "n_expected_gaps": len(case.expected_gaps),
                "n_expected_refs": len(case.expected_evidence_references),
                "n_expected_topics": len(case.expected_topics),
                "n_expected_methods": len(case.expected_methods),
            }
        )
    return stats


def _provider_config() -> dict[str, str]:
    from app.providers.embeddings.factory import get_embedding_provider
    from app.providers.literature.factory import get_literature_chain
    from app.providers.llm.factory import get_llm_provider

    try:
        llm = get_llm_provider()
        llm_name = getattr(llm, "name", type(llm).__name__)
    except Exception as exc:  # pragma: no cover
        llm_name = f"error: {exc}"
    try:
        emb = get_embedding_provider()
        emb_name = getattr(emb, "name", type(emb).__name__)
    except Exception:
        emb_name = "unknown"
    try:
        lit = get_literature_chain()
        lit_names = list(getattr(lit, "provider_names", None) or ["unknown"])
    except Exception:
        lit_names = ["unknown"]
    return {
        "llm_provider": llm_name,
        "embedding_provider": emb_name,
        "literature_chain": lit_names,
    }


async def _run_one(system_name: str, case, seed: int | None = None) -> CaseSystemRun:
    import time

    system = get_system(system_name, seed=seed)
    started = time.perf_counter()
    try:
        output = await system.run(case)
    except Exception as exc:
        return CaseSystemRun(
            status="error",
            error=f"{type(exc).__name__}: {exc}",
            duration_ms=(time.perf_counter() - started) * 1000,
        )
    metrics = compute_automatic_metrics(output, case)
    return CaseSystemRun(
        status="ok", metrics=metrics, output=output,
        duration_ms=(time.perf_counter() - started) * 1000,
    )


async def run_evaluation(
    *,
    dataset_path: str | Path,
    systems: list[str] | None = None,
    out_dir: str | Path,
    human_path: str | Path | None = None,
    limit: int | None = None,
    case_ids: list[str] | None = None,
    seed: int = 0,
    outputs_path: str | Path | None = None,
) -> dict[str, Any]:
    """Run the full evaluation; writes JSON/CSV/report into ``out_dir``.

    ``outputs_path`` optionally persists the normalized per-case/per-system
    outputs as JSON (used by the immutable per-seed experiment layout).
    ``case_ids`` selects an explicit subset of cases (after ``limit`` when
    both are given, the explicit subset wins).
    """
    ds = load_dataset(dataset_path)
    systems = systems or list(DEFAULT_SYSTEMS)
    for s in systems:
        get_system(s, seed=seed)  # validate early (ignore returned instance)

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    if case_ids:
        by_id = {c.case_id: c for c in ds.cases}
        missing = [cid for cid in case_ids if cid not in by_id]
        if missing:
            raise ValueError(
                f"Unknown case_ids requested: {missing}. "
                f"Available: {sorted(by_id)}"
            )
        cases = [by_id[cid] for cid in case_ids]
    elif limit:
        cases = ds.cases[:limit]
    else:
        cases = ds.cases
    outputs_by_case: dict[str, dict[str, Any]] = {}
    case_results: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []

    for case in cases:
        per_system: dict[str, dict[str, Any]] = {}
        outputs_by_case[case.case_id] = {}
        for system_name in systems:
            run = await _run_one(system_name, case, seed=seed)
            metrics = run.metrics if run.status == "ok" else {}
            if run.status == "ok":
                outputs_by_case[case.case_id][system_name] = run.output
            per_system[system_name] = {
                "status": run.status,
                "error": run.error,
                "metrics": metrics,
                "duration_ms": round(run.duration_ms, 3),
            }
            if run.status == "error":
                failures.append({"case_id": case.case_id, "system": system_name, "error": run.error or ""})
        case_results.append(
            {"case_id": case.case_id, "label": case.label, "systems": per_system}
        )

    aggregates = {
        s: aggregate_system(s, [c["systems"][s]["metrics"] for c in case_results if s in c["systems"]])
        for s in systems
    }

    # --- blind human evaluation -------------------------------------------
    blind_key = make_blind_key(outputs_by_case, seed=seed)
    _write_json(blind_key, out / "blind_key.json")

    human: dict[str, Any] = {"provided": False, "ratings_count": 0, "aggregates": None}
    if human_path and Path(human_path).exists():
        rows = load_human_ratings(human_path)
        human = {
            "provided": True,
            "ratings_count": len(rows),
            "aggregates": aggregate_human_ratings(rows, blind_key),
            "inter_rater": inter_rater_reliability(rows),
            "_rows": rows,
        }

    # --- structured failure analysis --------------------------------------
    failure_analysis = analyze_failures(ds, case_results, outputs_by_case)
    failure_summary = summarize_failures(failure_analysis)
    _write_json(failure_analysis, out / "failure_analysis.json")

    report_path = out / "report.md"
    from evaluation.report import build_report

    build_report(
        dataset=ds,
        case_stats=dataset_stats(ds),
        config=_build_config_meta(systems, seed=seed),
        case_results=case_results,
        aggregates=aggregates,
        human=human,
        failures=failures,
        failure_analysis=failure_analysis,
        inter_rater=human.get("inter_rater") if human.get("provided") else None,
        out_path=report_path,
    )

    template_path = out / "human_ratings_template.csv"
    if not human["provided"]:
        export_human_template(outputs_by_case, template_path, seed=seed)
        human["template_path"] = str(template_path)
        human["blind_key_path"] = str(out / "blind_key.json")

    results = {
        "dataset": {
            "dataset_id": ds.dataset_id,
            "version": ds.version,
            "label": ds.label,
            "provenance": ds.provenance,
            "is_synthetic": ds.is_synthetic,
            "description": ds.description,
            "created_utc": ds.created_utc,
            "source_providers": ds.source_providers,
            "annotation_provenance": ds.annotation_provenance,
            "content_sha256": ds.content_sha256,
            "n_cases": len(cases),
            "case_stats": dataset_stats(ds),
        },
        "config": _build_config_meta(systems, seed=seed),
        "cases": case_results,
        "aggregates": aggregates,
        "human": {
            "provided": human["provided"],
            "ratings_count": human["ratings_count"],
            "aggregates": human["aggregates"],
            "inter_rater": human.get("inter_rater"),
        },
        "failure_analysis": failure_analysis,
        "failure_summary": failure_summary,
        "blind_key": blind_key,
        "failures": failures,
        "generated_utc": utc_now_iso(),
    }
    _write_json(results, out / "results.json")
    _write_csv(results, out / "results.csv")
    if outputs_path is not None:
        _write_json(_outputs_as_dict(outputs_by_case), outputs_path)
    return results


def _build_config_meta(systems: list[str], seed: int | None = None) -> dict[str, Any]:
    from evaluation.environment import offline_mode

    return {
        "systems": systems,
        "seed": seed,
        "providers": _provider_config(),
        "offline_mode": offline_mode(),
        "generated_utc": utc_now_iso(),
    }


def _outputs_as_dict(outputs_by_case: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Normalized outputs -> JSON-safe dict (Pydantic models via model_dump)."""
    return {
        case_id: {
            system_name: (
                output.model_dump() if not isinstance(output, dict) else output
            )
            for system_name, output in per_system.items()
        }
        for case_id, per_system in outputs_by_case.items()
    }


def _write_json(payload: dict[str, Any], path: Path) -> None:
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def _write_csv(results: dict[str, Any], path: Path) -> None:
    rows = []
    for case in results["cases"]:
        for system_name, run in case["systems"].items():
            for metric in AUTOMATIC_METRICS:
                key = metric["key"]
                value = run["metrics"].get(key) if run["status"] == "ok" else None
                rows.append(
                    {
                        "dataset_id": results["dataset"]["dataset_id"],
                        "case_id": case["case_id"],
                        "system": system_name,
                        "metric": key,
                        "metric_label": metric["label"],
                        "kind": "automatic",
                        "requires_human": metric["requires_human"],
                        "value": "" if value is None else f"{value:.4f}",
                    }
                )
    for dim in HUMAN_RATINGS:
        for system_name in results["config"]["systems"]:
            rows.append(
                {
                    "dataset_id": results["dataset"]["dataset_id"],
                    "case_id": "*",
                    "system": system_name,
                    "metric": dim,
                    "metric_label": f"human_{dim}",
                    "kind": "human",
                    "requires_human": True,
                    "value": "pending",
                }
            )
    fieldnames = [
        "dataset_id", "case_id", "system", "metric",
        "metric_label", "kind", "requires_human", "value",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="evaluation.run",
        description="Run the ResearchCollision evaluation framework.",
    )
    parser.add_argument("--dataset", required=True, help="Path to dataset JSON.")
    parser.add_argument(
        "--systems",
        default=",".join(DEFAULT_SYSTEMS),
        help="Comma-separated systems to evaluate "
             f"(default: {','.join(DEFAULT_SYSTEMS)}).",
    )
    parser.add_argument("--out-dir", default="evaluation_out", help="Output directory.")
    parser.add_argument("--human", default=None, help="Optional human-ratings CSV/JSON.")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of cases.")
    parser.add_argument(
        "--seed", type=int, default=0,
        help="Reproducibility seed (default: 0). Controls random blind evaluation "
             "ids and, where the LLM endpoint supports it, deterministic sampling.",
    )
    args = parser.parse_args(argv)

    systems = [s.strip() for s in args.systems.split(",") if s.strip()]
    asyncio.run(
        run_evaluation(
            dataset_path=args.dataset,
            systems=systems,
            out_dir=args.out_dir,
            human_path=args.human,
            limit=args.limit,
            seed=args.seed,
        )
    )
    print(f"Evaluation complete. Artifacts written to {args.out_dir}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())