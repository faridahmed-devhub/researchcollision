"""Dataset schema validation for the evaluation framework."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from evaluation.runner import load_dataset
from evaluation.schemas import EvaluationDataset, SourcePaper

FIXTURE = Path(__file__).resolve().parents[1] / "evaluation" / "data" / "demo_discovery.json"


def _paper(paper_id: str, title: str) -> SourcePaper:
    return SourcePaper(paper_id=paper_id, title=title, abstract="An abstract about topic x.")


def test_fixture_is_loaded_and_synthetic():
    ds = load_dataset(FIXTURE)
    assert len(ds.cases) == 2
    assert ds.is_synthetic is True
    assert ds.provenance == "synthetic_fixture"
    assert ds.label.startswith("SYNTHETIC")
    for case in ds.cases:
        assert case.case_id
        assert case.researcher_a.name
        paper_ids = {p.paper_id for p in case.source_papers}
        assert len(paper_ids) == len(case.source_papers), "duplicate source_paper ids"
        assert set(case.expected_evidence_references) <= paper_ids
        for gap in case.expected_gaps:
            assert set(gap.evidence_paper_ids) <= paper_ids
        for r in (case.researcher_a, case.researcher_b):
            assert set(r.papers) <= paper_ids


def test_duplicate_case_ids_rejected():
    with pytest.raises(ValidationError):
        EvaluationDataset(
            dataset_id="d",
            is_synthetic=True,
            cases=[
                {"case_id": "a", "researcher_a": {"name": "A"}, "source_papers": []},
                {"case_id": "a", "researcher_a": {"name": "B"}, "source_papers": []},
            ],
        )


def test_expected_evidence_reference_must_exist_in_source_papers():
    with pytest.raises(ValidationError):
        EvaluationDataset(
            dataset_id="d",
            is_synthetic=True,
            cases=[
                {
                    "case_id": "a",
                    "researcher_a": {"name": "A"},
                    "source_papers": [_paper("p1", "Title One").model_dump()],
                    "expected_evidence_references": ["p-missing"],
                }
            ],
        )


def test_gap_evidence_refs_must_exist_in_source_papers():
    with pytest.raises(ValidationError):
        EvaluationDataset(
            dataset_id="d",
            is_synthetic=True,
            cases=[
                {
                    "case_id": "a",
                    "researcher_a": {"name": "A"},
                    "source_papers": [_paper("p1", "Title One").model_dump()],
                    "expected_gaps": [
                        {"gap_id": "g1", "description": "x", "evidence_paper_ids": ["ghost"]}
                    ],
                }
            ],
        )


def test_non_synthetic_dataset_is_allowed_with_curated_provenance():
    ds = EvaluationDataset(
        dataset_id="d2",
        provenance="curated",
        is_synthetic=False,
        cases=[{"case_id": "a", "researcher_a": {"name": "A"}, "source_papers": []}],
    )
    assert ds.is_synthetic is False


def test_synthetic_dataset_must_have_synthetic_label():
    with pytest.raises(ValidationError):
        EvaluationDataset(
            dataset_id="d3",
            is_synthetic=True,
            label="Real results",
            cases=[{"case_id": "a", "researcher_a": {"name": "A"}, "source_papers": []}],
        )


def test_fixture_rejects_malformed_json():
    import tempfile

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump({"dataset_id": "x", "cases": "not-a-list"}, f)
        fname = f.name
    try:
        with pytest.raises(ValidationError):
            load_dataset(fname)
    finally:
        Path(fname).unlink(missing_ok=True)