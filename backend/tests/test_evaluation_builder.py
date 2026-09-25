"""Reproducible real-dataset builder (with an injected fake provider)."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.providers.literature.base import PaperMetadata
from evaluation.build_real_dataset import build_case, build_dataset, load_specs

SPECS = Path(__file__).resolve().parents[1] / "evaluation" / "data" / "real_case_specs_v1.json"


class FakeProvider:
    name = "fakeprov"

    def __init__(self, by_query):
        self._by_query = by_query

    async def search(self, query, *, limit=10):
        return self._by_query.get(query, [])[:limit]


def _meta(i, **over):
    base = {
        "title": f"Paper {i}",
        "abstract": f"Abstract {i} on a research topic",
        "provider_id": f"W{i}",
        "doi": f"10.0/{i}",
        "year": 2020,
        "citation_count": i,
        "topics": ["topic-a", "topic-b"],
        "authors": ["Author"],
    }
    base.update(over)
    return PaperMetadata(**base)


def _spec():
    return {
        "case_id": "c1",
        "domain_a": "Domain A",
        "query_a": "qa",
        "domain_b": "Domain B",
        "query_b": "qb",
        "field_query": "qa qb",
        "evaluation_question": "Which direction connects A and B?",
    }


async def test_build_dataset_produces_traceable_non_synthetic_dataset():
    specs = {"dataset_id": "d", "version": "2.0.0", "description": "x", "domain_pairs": [_spec()]}
    provider = FakeProvider({"qa": [_meta(1), _meta(2), _meta(3)], "qb": [_meta(4), _meta(5)]})
    ds = await build_dataset(specs, provider, min_papers=4)

    assert ds.is_synthetic is False
    assert ds.version == "2.0.0"
    assert ds.source_providers == ["fakeprov"]
    assert ds.content_sha256 == ds.compute_content_sha256()
    assert ds.annotation_provenance["expected_gaps"] == "none"

    case = ds.cases[0]
    assert case.evaluation_question == "Which direction connects A and B?"
    assert case.researcher_a.name == "Domain A"
    assert len(case.source_papers) == 5
    assert all(p.provider_id and p.evidence_text for p in case.source_papers)
    # heuristic reference set = most-cited papers, labeled machine-generated
    assert case.expected_evidence_references == ["W5", "W4", "W3"]
    assert case.expected_evidence_source == "machine_generated"
    assert case.expected_gaps == []


async def test_builder_drops_unusable_records_and_refuses_to_fabricate():
    provider = FakeProvider({
        "qa": [
            _meta(1),
            PaperMetadata(title="No abstract", abstract=None, provider_id="W9"),
            PaperMetadata(title="No id", abstract="x", provider_id="", doi=None),
        ],
        "qb": [_meta(2)],
    })
    with pytest.raises(RuntimeError, match="Refusing to fabricate"):
        await build_case(_spec(), provider, min_papers=3)


async def test_builder_single_case_insufficient_papers_raises():
    provider = FakeProvider({"qa": [_meta(1)], "qb": []})
    with pytest.raises(RuntimeError, match="only 1 usable real papers"):
        await build_case(_spec(), provider, min_papers=4)


def test_specs_file_defines_many_unique_real_cases():
    specs = load_specs(SPECS)
    pairs = specs["domain_pairs"]
    assert len(pairs) >= 10
    ids = [p["case_id"] for p in pairs]
    assert len(ids) == len(set(ids))
    for p in pairs:
        assert p["evaluation_question"]
        assert p["query_a"] and p["query_b"]
