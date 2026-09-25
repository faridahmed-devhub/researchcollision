"""Per-seed immutable experiment persistence (Phase 2B). Once a run is
*completed* (``run_manifest.json`` present with ``status: "completed"``) the
directory is immutable: re-running into an existing non-empty directory is a
hard error. Resume/logic for skipping completed seeds lives in the batch
runner (Phase 2C); this module never overwrites existing artifacts.

Layout per seed directory::

    run_manifest.json          # seed, status, timestamps, total runtime, contents
    config.json                # full resolved config snapshot (secrets redacted)
    prompt_versions.json       # {prompt file: {"sha256", "version"}}
    corpus_meta.json           # dataset provenance + corpus availability/access policy
    status.json                # per case/system status, error, duration_ms, totals
    results.json               # normalized results (from evaluation.runner)
    results.csv
    report.md
    failure_analysis.json
    failures.json              # plain list of {case_id, system, error}
    blind_key.json             # seed-dependent blind mapping (if no ratings)
    human_ratings_template.csv # (if no ratings provided)
    outputs_per_case.json      # normalized per-case/per-system outputs
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from evaluation.runner import load_dataset, run_evaluation

EXPERIMENTS_ROOT = Path(__file__).resolve().parents[1] / "experiments" / "v2"

# Applied/reference retry policy (must match app/providers/llm/openai_compatible.py).
from app.providers.llm.openai_compatible import _RETRYABLE_STATUSES

RETRY_POLICY = {
    "max_attempts": 3,
    "retryable_statuses": sorted(_RETRYABLE_STATUSES),
    "wait_exponential": {"multiplier": 1, "min_seconds": 2, "max_seconds": 15},
}

_SECRET_FIELDS = {
    "openai_api_key",
    "openrouter_api_key",
    "semantic_scholar_api_key",
    "secret_key",
}


class ExperimentError(RuntimeError):
    """Raised when a seed directory already contains artifacts (immutability)."""


def seed_dir(root: Path = EXPERIMENTS_ROOT, seed: int = 0) -> Path:
    return root / f"seed{seed}"


def is_completed(dir_path: Path) -> bool:
    manifest = dir_path / "run_manifest.json"
    if not manifest.exists():
        return False
    try:
        return json.loads(manifest.read_text(encoding="utf-8")).get("status") == "completed"
    except (json.JSONDecodeError, OSError):
        return False


def _prompt_file_hashes() -> dict[str, str]:
    from app.agents.base import PROMPTS_DIR

    out: dict[str, str] = {}
    for p in sorted(PROMPTS_DIR.glob("*.txt")):
        out[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def collect_prompt_versions() -> dict[str, dict[str, str]]:
    from evaluation.prompt_registry import agent_prompt_versions

    hashes = _prompt_file_hashes()
    registry = agent_prompt_versions()
    return {
        name: {
            "sha256": hashes.get(name, "MISSING"),
            "version": registry.get(name, {}).get("version", "unknown"),
            "agent": registry.get(name, {}).get("agent", "unknown"),
        }
        for name in sorted(set(hashes) | set(registry))
    }


def config_snapshot(
    *,
    seed: int,
    systems: list[str],
    dataset_path: str | Path,
    out_dir: str | Path,
    limit: int | None,
) -> dict[str, Any]:
    from app.core.config import settings
    from evaluation.environment import offline_mode

    try:
        raw_settings = settings.model_dump(mode="json")
    except Exception:  # pragma: no cover - never break artifact writing
        raw_settings = {}
    redacted = {k: ("<redacted>" if k in _SECRET_FIELDS and v else v) for k, v in raw_settings.items()}
    return {
        "seed": seed,
        "systems": systems,
        "dataset_path": str(dataset_path),
        "out_dir": str(out_dir),
        "limit": limit,
        "offline_mode": offline_mode(),
        "retry_policy": RETRY_POLICY,
        "settings": redacted,
    }


def corpus_meta(dataset_path: str | Path, case_ids: list[str] | None = None) -> dict[str, Any]:
    ds = load_dataset(dataset_path)
    return {
        "dataset_id": ds.dataset_id,
        "version": ds.version,
        "label": ds.label,
        "is_synthetic": ds.is_synthetic,
        "source_providers": ds.source_providers,
        "annotation_provenance": ds.annotation_provenance,
        "description": ds.description,
        "created_utc": ds.created_utc,
        "content_sha256": ds.content_sha256,
        "n_cases": len(ds.cases),
        "case_ids_requested": case_ids,
        "n_cases_requested": len(case_ids) if case_ids else None,
        "providers": {
            "llm_provider": "see config.json (resolved providers)",
            "embedding_provider": "see config.json",
            "literature_chain": "see config.json",
        },
        "access_dates": {},
        "access_dates_note": (
            "Retrieval access dates are recorded at query time during data build "
            "(Phase 3) and repeated runs (Phase 5). None recorded for pilot v1."
        ),
    }


def _status_payload(results: dict[str, Any]) -> dict[str, Any]:
    per_case: dict[str, Any] = {}
    n_ok = n_error = 0
    for case in results["cases"]:
        for sysname, run in case["systems"].items():
            per_case.setdefault(case["case_id"], {})[sysname] = {
                "status": run["status"],
                "error": run.get("error"),
                "duration_ms": run.get("duration_ms"),
            }
            if run["status"] == "ok":
                n_ok += 1
            else:
                n_error += 1
    return {
        "per_case": per_case,
        "totals": {
            "n_cases": len(results["cases"]),
            "n_case_system_runs": n_ok + n_error,
            "n_ok": n_ok,
            "n_error": n_error,
            "retry_policy": RETRY_POLICY,
        },
    }


def _write_json(payload: dict[str, Any], path: Path) -> None:
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


async def run_immutable_seed(
    *,
    dataset_path: str | Path,
    systems: list[str] | None = None,
    seed: int = 0,
    root: Path = EXPERIMENTS_ROOT,
    human_path: str | Path | None = None,
    limit: int | None = None,
    case_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Run one seed into ``root/seed<seed>/``; refuse to touch non-empty dirs."""
    from datetime import datetime, timezone

    from evaluation.baselines import DEFAULT_SYSTEMS

    systems = systems or list(DEFAULT_SYSTEMS)
    folder = seed_dir(root, seed)
    folder.mkdir(parents=True, exist_ok=True)
    if any(folder.iterdir()):
        raise ExperimentError(
            f"Seed directory {folder} already contains artifacts and is immutable. "
            "Choose a different seed, or inspect the existing run (never overwrite)."
        )

    started_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")
    started = time.perf_counter()
    results = await run_evaluation(
        dataset_path=dataset_path,
        systems=systems,
        out_dir=folder,
        human_path=human_path,
        limit=limit,
        case_ids=case_ids,
        seed=seed,
        outputs_path=folder / "outputs_per_case.json",
    )
    total_seconds = round(time.perf_counter() - started, 3)
    finished_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")

    _write_json(config_snapshot(
        seed=seed, systems=systems, dataset_path=dataset_path, out_dir=folder, limit=limit,
    ), folder / "config.json")
    _write_json(collect_prompt_versions(), folder / "prompt_versions.json")
    _write_json(corpus_meta(dataset_path, case_ids), folder / "corpus_meta.json")
    _write_json(_status_payload(results), folder / "status.json")
    _write_json({"failures": results["failures"]}, folder / "failures.json")

    contents = sorted(
        (p.name, p.stat().st_size)
        for p in folder.iterdir()
        if p.is_file()
    )
    manifest = {
        "seed": seed,
        "status": "completed",
        "started_utc": started_utc,
        "finished_utc": finished_utc,
        "total_seconds": total_seconds,
        "dataset_path": str(dataset_path),
        "systems": systems,
        "case_ids": case_ids,
        "n_cases": results["dataset"]["n_cases"],
        "contents": [{"name": name, "bytes": size} for name, size in contents],
        "raw_traces_note": (
            "Raw LLM request/response traces are not captured yet (provider-level "
            "instrumentation lands in Phase 4). Normalized outputs are persisted in "
            "outputs_per_case.json; failures are never hidden (failures.json)."
        ),
    }
    _write_json(manifest, folder / "run_manifest.json")
    return {
        **results,
        "_seed_dir": str(folder),
        "total_seconds": total_seconds,
        "started_utc": started_utc,
        "finished_utc": finished_utc,
    }


def main(argv: list[str] | None = None) -> int:
    import argparse
    import asyncio

    from evaluation.baselines import DEFAULT_SYSTEMS
    from evaluation.environment import configure_offline_defaults

    configure_offline_defaults()

    parser = argparse.ArgumentParser(
        prog="evaluation.experiment",
        description="Run a single seed into an immutable experiments/v2/seed<N>/ directory.",
    )
    parser.add_argument("--dataset", required=True, help="Path to dataset JSON.")
    parser.add_argument(
        "--systems",
        default=",".join(DEFAULT_SYSTEMS),
        help=f"Comma-separated systems (default: {','.join(DEFAULT_SYSTEMS)}).",
    )
    parser.add_argument("--seed", type=int, default=0, help="Seed index (default: 0).")
    parser.add_argument("--root", default=str(EXPERIMENTS_ROOT), help="Experiments root.")
    parser.add_argument("--human", default=None, help="Optional human-ratings CSV/JSON.")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of cases.")
    parser.add_argument("--case-ids", default=None, help="Comma-separated case ids to run.")
    args = parser.parse_args(argv)

    systems = [s.strip() for s in args.systems.split(",") if s.strip()]
    case_ids = [c.strip() for c in args.case_ids.split(",") if c.strip()] if args.case_ids else None
    asyncio.run(run_immutable_seed(
        dataset_path=args.dataset,
        systems=systems,
        seed=args.seed,
        root=Path(args.root),
        human_path=args.human,
        limit=args.limit,
        case_ids=case_ids,
    ))
    print(f"Seed {args.seed} complete. Artifacts at {seed_dir(Path(args.root), args.seed)}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())