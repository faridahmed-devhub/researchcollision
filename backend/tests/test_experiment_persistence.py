"""Phase 2B: per-seed immutable experiment persistence."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from evaluation.experiment import (
    ExperimentError,
    is_completed,
    run_immutable_seed,
    seed_dir,
)

FIXTURE = Path(__file__).resolve().parents[1] / "evaluation" / "data" / "demo_discovery.json"


@pytest.mark.slow
async def test_run_immutable_seed_builds_full_layout(tmp_path):
    root = tmp_path / "exp"
    results = await run_immutable_seed(
        dataset_path=FIXTURE,
        systems=["keyword", "embedding", "llm_only", "pipeline"],
        seed=0,
        root=root,
    )
    folder = seed_dir(root, 0)
    assert results["_seed_dir"] == str(folder)
    assert is_completed(folder)

    expected = {
        "run_manifest.json", "config.json", "prompt_versions.json", "corpus_meta.json",
        "status.json", "results.json", "results.csv", "report.md",
        "failure_analysis.json", "failures.json", "blind_key.json",
        "human_ratings_template.csv", "outputs_per_case.json",
    }
    present = {p.name for p in folder.iterdir() if p.is_file()}
    assert expected <= present, f"missing {expected - present}"

    manifest = json.loads((folder / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "completed"
    assert manifest["seed"] == 0
    assert manifest["total_seconds"] >= 0
    assert manifest["n_cases"] == 2

    config = json.loads((folder / "config.json").read_text(encoding="utf-8"))
    assert config["seed"] == 0
    assert config["retry_policy"]["max_attempts"] == 3
    assert config["settings"]["openai_api_key"] == "<redacted>"

    prompts = json.loads((folder / "prompt_versions.json").read_text(encoding="utf-8"))
    assert prompts and all("sha256" in v for v in prompts.values())

    corpus = json.loads((folder / "corpus_meta.json").read_text(encoding="utf-8"))
    assert corpus["dataset_id"]
    assert corpus["is_synthetic"] is True
    assert "access_dates_note" in corpus

    status = json.loads((folder / "status.json").read_text(encoding="utf-8"))
    assert status["totals"]["n_case_system_runs"] == 2 * 4
    assert status["totals"]["n_error"] == 0
    for run in status["per_case"].values():
        for sysinfo in run.values():
            assert sysinfo["status"] == "ok"
            assert isinstance(sysinfo["duration_ms"], (int, float))

    outputs = json.loads((folder / "outputs_per_case.json").read_text(encoding="utf-8"))
    assert set(outputs) == set(status["per_case"])
    case_id = next(iter(outputs))
    assert "llm_only" in outputs[case_id]
    assert set(outputs[case_id]["llm_only"]) == {"system", "kind", "gaps", "intersections", "hypotheses", "known_context_titles"}

    failures = json.loads((folder / "failures.json").read_text(encoding="utf-8"))
    assert failures["failures"] == []


async def test_immutable_dir_refuses_overwrite(tmp_path):
    root = tmp_path / "exp"
    await run_immutable_seed(dataset_path=FIXTURE, systems=["keyword"], seed=0, root=root)
    with pytest.raises(ExperimentError, match="immutable"):
        await run_immutable_seed(dataset_path=FIXTURE, systems=["keyword"], seed=0, root=root)
    # a different seed writes into its own fresh directory
    await run_immutable_seed(dataset_path=FIXTURE, systems=["keyword"], seed=1, root=root)
    assert is_completed(seed_dir(root, 0))
    assert is_completed(seed_dir(root, 1))


def test_is_completed_on_empty_and_fresh(tmp_path):
    assert not is_completed(tmp_path)
    d = tmp_path / "sub"
    d.mkdir()
    (d / "run_manifest.json").write_text('{"status": "completed"}', encoding="utf-8")
    assert is_completed(d)


# ---------------------------------------------------------------------------
# Phase 2C: batch runner + case selection
# ---------------------------------------------------------------------------


async def test_run_batch_completes_and_resume_skips(tmp_path):
    from evaluation.batch import run_batch

    root = tmp_path / "exp"
    m0 = await run_batch(dataset_path=FIXTURE, seeds=[0, 1], systems=["keyword", "llm_only"], root=root)
    assert m0["summary"]["completed"] == 2
    assert m0["summary"]["errors"] == 0
    assert is_completed(seed_dir(root, 0))
    assert is_completed(seed_dir(root, 1))

    m1 = await run_batch(
        dataset_path=FIXTURE, seeds=[0, 1, 2], systems=["keyword", "llm_only"],
        root=root, resume=True,
    )
    by_seed = {r["seed"]: r["status"] for r in m1["records"]}
    assert by_seed[0] == "skipped_completed"
    assert by_seed[1] == "skipped_completed"
    assert by_seed[2] == "completed"
    assert m1["summary"]["skipped_completed"] == 2

    m2 = await run_batch(dataset_path=FIXTURE, seeds=[0], systems=["keyword", "llm_only"], root=root)
    assert m2["records"][0]["status"] == "already_exists_no_resume"
    assert m2["summary"]["errors"] == 1


async def test_batch_writes_machine_readable_manifest(tmp_path):
    from evaluation.batch import run_batch

    root = tmp_path / "exp"
    await run_batch(dataset_path=FIXTURE, seeds=[3], systems=["keyword"], root=root)
    manifests = list((root / "_batch_manifests").glob("batch_*.json"))
    assert len(manifests) == 1
    data = json.loads(manifests[0].read_text(encoding="utf-8"))
    assert data["kind"] == "batch_manifest"
    assert data["summary"]["completed"] == 1
    assert data["records"][0]["status"] == "completed"


async def test_immutable_seed_respects_case_selection(tmp_path):
    root = tmp_path / "exp"
    results = await run_immutable_seed(
        dataset_path=FIXTURE, systems=["keyword"], seed=0, root=root,
        case_ids=["nlp_x_speech"],
    )
    assert results["dataset"]["n_cases"] == 1
    assert [c["case_id"] for c in results["cases"]] == ["nlp_x_speech"]


async def test_immutable_seed_rejects_unknown_case_ids(tmp_path):
    with pytest.raises(ValueError, match="Unknown case_ids"):
        await run_immutable_seed(
            dataset_path=FIXTURE, systems=["keyword"], seed=0,
            root=tmp_path / "exp", case_ids=["does_not_exist"],
        )