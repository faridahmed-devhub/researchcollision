"""Batch runner for per-seed immutable experiments (Phase 2C).

Runs the selected seeds sequentially. Each seed is executed through
``run_immutable_seed`` into ``root/seed<N>/``; completed seeds are detected via
``run_manifest.json`` and skipped when ``--resume`` is passed. Seed directories
are never overwritten. A machine-readable batch manifest is written to
``root/_batch_manifests/batch_<timestamp>.json`` and printed as a summary.

Example (from the backend directory)::

    python -m evaluation.batch --dataset evaluation/data/real_case_study_v1.json \
        --seeds 0 1 2 3 4 --systems keyword,embedding,llm_only,pipeline \
        --root experiments/v2 --resume
"""
from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evaluation.environment import configure_offline_defaults
from evaluation.experiment import (
    EXPERIMENTS_ROOT,
    is_completed,
    run_immutable_seed,
    seed_dir,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


async def run_batch(
    *,
    dataset_path: str | Path,
    seeds: list[int],
    systems: list[str] | None = None,
    root: Path = EXPERIMENTS_ROOT,
    human_path: str | Path | None = None,
    limit: int | None = None,
    case_ids: list[str] | None = None,
    resume: bool = False,
) -> dict[str, Any]:
    """Run ``seeds`` sequentially; skip completed ones when ``resume`` is set."""
    started = _utc_now()
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, Any]] = []
    for seed in seeds:
        folder = seed_dir(root, seed)
        done = is_completed(folder)
        if done and resume:
            records.append({"seed": seed, "status": "skipped_completed", "seed_dir": str(folder)})
            continue
        if done:
            records.append({
                "seed": seed, "status": "already_exists_no_resume",
                "seed_dir": str(folder), "error": "run_manifest.json present; pass --resume to skip",
            })
            continue
        if folder.exists() and any(folder.iterdir()):
            records.append({
                "seed": seed, "status": "partial_dir_blocked", "seed_dir": str(folder),
                "error": "directory is non-empty but has no completed manifest; never overwrite",
            })
            continue
        try:
            results = await run_immutable_seed(
                dataset_path=dataset_path,
                systems=systems,
                seed=seed,
                root=root,
                human_path=human_path,
                limit=limit,
                case_ids=case_ids,
            )
            records.append({
                "seed": seed, "status": "completed", "seed_dir": str(folder),
                "n_cases": results["dataset"]["n_cases"],
                "total_seconds": results.get("total_seconds"),
            })
        except Exception as exc:
            records.append({
                "seed": seed, "status": "error", "seed_dir": str(folder),
                "error": f"{type(exc).__name__}: {exc}",
            })

    manifest = {
        "kind": "batch_manifest",
        "started_utc": started,
        "finished_utc": _utc_now(),
        "dataset_path": str(dataset_path),
        "systems": systems,
        "seeds_requested": seeds,
        "resume": resume,
        "records": records,
        "summary": {
            "completed": sum(1 for r in records if r["status"] == "completed"),
            "skipped_completed": sum(1 for r in records if r["status"] == "skipped_completed"),
            "errors": sum(1 for r in records if r["status"] in ("error", "partial_dir_blocked", "already_exists_no_resume")),
        },
    }
    manifests_dir = root / "_batch_manifests"
    manifests_dir.mkdir(parents=True, exist_ok=True)
    path = manifests_dir / f"batch_{started.replace(':', '-')}.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    from evaluation.baselines import DEFAULT_SYSTEMS

    configure_offline_defaults()

    parser = argparse.ArgumentParser(
        prog="evaluation.batch",
        description="Run per-seed immutable experiments sequentially.",
    )
    parser.add_argument("--dataset", required=True, help="Path to dataset JSON.")
    parser.add_argument(
        "--seeds", required=True,
        help="Seed indices, e.g. `0 1 2 3 4` or `--seeds 0 --seeds 1`.",
    )
    parser.add_argument(
        "--systems",
        default=",".join(DEFAULT_SYSTEMS),
        help=f"Comma-separated systems (default: {','.join(DEFAULT_SYSTEMS)}).",
    )
    parser.add_argument("--root", default=str(EXPERIMENTS_ROOT), help="Experiments root.")
    parser.add_argument("--human", default=None, help="Optional human-ratings CSV/JSON.")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of cases.")
    parser.add_argument("--case-ids", default=None, help="Comma-separated case ids.")
    parser.add_argument(
        "--resume", action="store_true",
        help="Skip seeds whose seed directory already has a completed run_manifest.json.",
    )
    args = parser.parse_args(argv)

    seeds = [int(s.strip()) for s in args.seeds.split(",") if s.strip()]
    systems = [s.strip() for s in args.systems.split(",") if s.strip()]
    case_ids = [c.strip() for c in args.case_ids.split(",") if c.strip()] if args.case_ids else None

    manifest = asyncio.run(run_batch(
        dataset_path=args.dataset,
        seeds=seeds,
        systems=systems,
        root=Path(args.root),
        human_path=args.human,
        limit=args.limit,
        case_ids=case_ids,
        resume=args.resume,
    ))
    for record in manifest["records"]:
        status = record["status"]
        line = f"  seed {record['seed']}: {status}"
        if record.get("error"):
            line += f"  ({record['error']})"
        print(line)
    print(
        f"\nBatch done: {manifest['summary']['completed']} completed, "
        f"{manifest['summary']['skipped_completed']} skipped (resume), "
        f"{manifest['summary']['errors']} errors."
    )
    return 0 if manifest["summary"]["errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())