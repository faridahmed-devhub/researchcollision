"""Validation of the committed real case-study dataset (offline, file-only)."""
from __future__ import annotations

from pathlib import Path

import pytest

from evaluation.metrics import research_gap_relevance
from evaluation.runner import load_dataset
from evaluation.schemas import ANNOTATION_SOURCES, SystemGap, SystemOutput

REAL = Path(__file__).resolve().parents[1] / "evaluation" / "data" / "real_case_study_v1.json"

pytestmark = pytest.mark.skipif(not REAL.exists(), reason="real dataset not built")


@pytest.fixture(scope="module")
def ds():
    return load_dataset(REAL)


def test_real_dataset_is_non_synthetic_and_traceable(ds):
    assert ds.is_synthetic is False
    assert ds.provenance == "curated"
    assert len(ds.cases) >= 10
    assert ds.content_sha256 == ds.compute_content_sha256()
    assert set(ds.annotation_provenance.values()) <= set(ANNOTATION_SOURCES)


def test_every_source_paper_is_publicly_traceable(ds):
    for case in ds.cases:
        assert case.evaluation_question
        assert len(case.source_papers) >= 4
        for p in case.source_papers:
            assert p.doi or p.provider_id, f"{case.case_id}/{p.paper_id} untraceable"
            assert p.evidence_text, f"{case.case_id}/{p.paper_id} has no evidence text"
            assert p.source_provider == "openalex"


def test_annotations_are_labeled_and_gaps_absent(ds):
    for case in ds.cases:
        assert case.expected_gaps == []
        assert case.expected_evidence_source == "machine_generated"
        assert case.expected_topics


def test_missing_gap_gold_is_reported_not_as_zero(ds):
    out = SystemOutput(system="x", gaps=[SystemGap(description="anything")])
    assert research_gap_relevance(out, ds.cases[0]) is None
