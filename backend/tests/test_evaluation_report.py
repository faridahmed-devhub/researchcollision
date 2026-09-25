"""Markdown report generation for the evaluation framework."""
from __future__ import annotations

from pathlib import Path

from evaluation.report import build_report
from evaluation.runner import load_dataset

FIXTURE = Path(__file__).resolve().parents[1] / "evaluation" / "data" / "demo_discovery.json"


def _base_payload(ds):
    return {
        "dataset": ds,
        "case_stats": [
            {"case_id": c.case_id, "n_source_papers": len(c.source_papers),
             "n_expected_gaps": len(c.expected_gaps),
             "n_expected_refs": len(c.expected_evidence_references),
             "n_expected_topics": len(c.expected_topics),
             "n_expected_methods": len(c.expected_methods)}
            for c in ds.cases
        ],
        "config": {
            "systems": ["keyword", "pipeline"],
            "providers": {"llm_provider": "mock", "embedding_provider": "mock",
                          "literature_chain": ["mock"]},
            "generated_utc": "2026-01-01T00:00:00+00:00",
        },
        "case_results": [],
        "aggregates": {
            "keyword": {"metrics": {"evidence_citation_validity": {"mean": 1.0, "min": 1.0, "max": 1.0, "n": 1}}},
            "pipeline": {"metrics": {"evidence_citation_validity": {"mean": 0.8, "min": 0.8, "max": 0.8, "n": 1}}},
        },
        "human": {"provided": False, "ratings_count": 0, "aggregates": None},
        "failures": [],
    }


def test_report_includes_all_required_sections(tmp_path):
    ds = load_dataset(FIXTURE)
    text = build_report(**_base_payload(ds), out_path=tmp_path / "report.md")
    for heading in [
        "## Dataset statistics",
        "## Automatic metrics",
        "## Per-case automatic metrics",
        "## Human evaluation",
        "## Limitations",
    ]:
        assert heading in text, f"missing {heading}"
    assert "SYNTHETIC EVALUATION FIXTURE" in text
    assert "no system failures" in text.lower()
    out = Path(tmp_path / "report.md")
    assert out.exists() and out.stat().st_size > 0


def test_report_does_not_fabricate_human_scores(tmp_path):
    ds = load_dataset(FIXTURE)
    text = build_report(**_base_payload(ds), out_path=tmp_path / "report.md")
    assert "Pending human annotation" in text
    # no numeric human dimension means/levels anywhere in the report
    assert "relevance | " not in text  # no human table rendered
    # the seed value above must never appear as a human score
    assert " 5.00 (n=" not in text


def test_report_shows_human_columns_only_when_provided(tmp_path):
    ds = load_dataset(FIXTURE)
    payload = _base_payload(ds)
    payload["human"] = {
        "provided": True,
        "ratings_count": 2,
        "aggregates": {
            "pipeline": {"relevance": {"mean": 4.5, "n": 2, "min": 4, "max": 5}},
        },
    }
    text = build_report(**payload, out_path=tmp_path / "report.md")
    assert "Raters provided 2 human rating rows" in text
    assert "4.50 (n=2)" in text
    assert "Pending human annotation" not in text


def test_report_lists_failures(tmp_path):
    ds = load_dataset(FIXTURE)
    payload = _base_payload(ds)
    payload["failures"] = [
        {"case_id": "c1", "system": "pipeline", "error": "ProviderError: boom"}
    ]
    text = build_report(**payload, out_path=tmp_path / "report.md")
    assert "ProviderError: boom" in text
    assert "c1" in text