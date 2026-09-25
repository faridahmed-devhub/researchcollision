"""End-to-end evaluation run (offline/mock) and human-template checks."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from evaluation.human import export_human_template, load_human_ratings
from evaluation.runner import run_evaluation

FIXTURE = Path(__file__).resolve().parents[1] / "evaluation" / "data" / "demo_discovery.json"


@pytest.mark.slow
async def test_run_evaluation_offline_produces_all_artifacts(tmp_path):
    results = await run_evaluation(
        dataset_path=FIXTURE,
        systems=["keyword", "embedding", "llm_only", "pipeline"],
        out_dir=tmp_path,
    )
    assert results["failures"] == []
    for p in (
        "results.json", "results.csv", "report.md", "human_ratings_template.csv",
        "blind_key.json", "failure_analysis.json",
    ):
        assert (tmp_path / p).exists(), f"missing artifact {p}"

    assert set(results["aggregates"]) == {"keyword", "embedding", "llm_only", "pipeline"}
    for system in results["aggregates"]:
        metrics = results["aggregates"][system]["metrics"]
        assert "evidence_citation_validity" in metrics
        assert "hallucination_rate" in metrics
        assert "experiment_design_completeness" in metrics

    # human scores were never fabricated
    assert results["human"]["provided"] is False
    assert results["human"]["aggregates"] is None
    assert results["human"]["ratings_count"] == 0

    # dataset provenance recorded
    assert results["dataset"]["is_synthetic"] is True
    assert "version" in results["dataset"]
    assert "annotation_provenance" in results["dataset"]

    # every case ran every system with status ok
    assert len(results["cases"]) == 2
    for case in results["cases"]:
        assert set(case["systems"]) == {"keyword", "embedding", "llm_only", "pipeline"}
        for name, run in case["systems"].items():
            assert run["status"] == "ok", f"{case['case_id']}/{name}: {run['error']}"

    # the blind key maps every rated item but carries system identity only there
    blind = json.loads((tmp_path / "blind_key.json").read_text(encoding="utf-8"))
    assert blind and all("system" in meta for meta in blind.values())


async def test_run_evaluation_respects_limit(tmp_path):
    results = await run_evaluation(
        dataset_path=FIXTURE,
        systems=["keyword"],
        out_dir=tmp_path,
        limit=1,
    )
    assert len(results["cases"]) == 1
    assert results["dataset"]["n_cases"] == 1


def test_csv_marks_human_metrics_as_pending(tmp_path):
    import asyncio

    asyncio.run(run_evaluation(dataset_path=FIXTURE, systems=["keyword"], out_dir=tmp_path))
    with (tmp_path / "results.csv").open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    human_rows = [r for r in rows if r["kind"] == "human"]
    assert len(human_rows) == 4  # one row per human dimension
    for r in human_rows:
        assert r["value"] == "pending"
        assert r["requires_human"] == "True"
    auto_keys = {r["metric"] for r in rows if r["kind"] == "automatic"}
    assert "evidence_grounding_precision" in auto_keys
    assert "hallucination_rate" in auto_keys


def test_human_template_is_blind(tmp_path):
    import asyncio

    from evaluation.human import TEMPLATE_COLUMNS

    _ = asyncio.run(run_evaluation(
        dataset_path=FIXTURE, systems=["pipeline"], out_dir=tmp_path
    ))
    # verify the exported template columns are blind (content only, no system/scores)
    with (tmp_path / "human_ratings_template.csv").open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    columns = list(rows[0].keys())
    assert columns == TEMPLATE_COLUMNS
    assert "system" not in columns
    assert "intersection_index" not in columns
    forbidden = {"novelty_confidence", "feasibility_confidence", "evidence_grounding_precision"}
    assert not (forbidden & set(columns))
    # every row carries a unique random eval_id and a surface
    ids = [r["eval_id"] for r in rows]
    assert len(ids) == len(set(ids))
    assert all(r["eval_id"].startswith("EV-") for r in rows)
    assert {r["surface"] for r in rows} <= {"gap", "intersection", "hypothesis"}
    assert all(rows)  # no empty spacer rows emitted


def test_human_ratings_validation(tmp_path):
    template = tmp_path / "t.csv"
    template.write_text(
        "eval_id,rater,case_id,surface,title,description,research_gap,evidence_references,"
        "relevance,novelty,plausibility,evidence_quality,notes\n"
        "EV-a,alice,c1,gap,,desc,,,\n"
        "EV-b,alice,c1,intersection,,desc,,,\n",
        encoding="utf-8",
    )
    # empty ratings load fine (pending)
    rows = load_human_ratings(template)
    assert len(rows) == 2
    assert rows[0]["relevance"] is None

    bad = tmp_path / "bad.csv"
    bad.write_text(
        "eval_id,rater,case_id,surface,title,description,research_gap,evidence_references,"
        "relevance,novelty,plausibility,evidence_quality,notes\n"
        "EV-a,alice,c1,gap,,desc,,,6,,,,\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="relevance rating 6 out of range"):
        load_human_ratings(bad)

    dup = tmp_path / "dup.csv"
    dup.write_text(
        "eval_id,rater,case_id,surface,title,description,research_gap,evidence_references,"
        "relevance,novelty,plausibility,evidence_quality,notes\n"
        "EV-a,alice,c1,gap,,desc,,,,4,,,,\n"
        "EV-a,alice,c1,gap,,desc,,,,5,,,,\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Duplicate rating row"):
        load_human_ratings(dup)


def test_export_human_template_never_includes_scores(tmp_path):
    # only intersection surface fields are allowed in the CSV export
    from evaluation.schemas import SystemIntersection, SystemOutput

    output = SystemOutput(
        system="pipeline",
        intersections=[SystemIntersection(
            title="IX", description="desc", research_gap="gap",
            evidence_refs=[],
        )],
    )
    out = tmp_path / "x.csv"
    export_human_template({"c1": {"pipeline": output}}, out)
    text = out.read_text(encoding="utf-8")
    assert "IX" in text and "desc" in text
    assert "novelty_confidence" not in text
    assert "0.55" not in text