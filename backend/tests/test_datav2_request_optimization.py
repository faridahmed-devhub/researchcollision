"""Offline tests locking in the per-domain OpenAlex query-cache optimization.

The frozen 96-pair frame references only 30 distinct OpenAlex query strings, so
fetching each query exactly once (instead of 2x96 per-candidate search calls,
plus 2x~60 at build time) is provably decision-equivalent for identical corpus
results, while cutting OpenAlex requests from ~312 to 30. No live requests.
"""
from __future__ import annotations

import json

import pytest

from app.providers.literature.base import PaperMetadata
from evaluation.datav2 import build as b
from evaluation.datav2 import sampling as s
from evaluation.datav2.build import _queries_in, _screen_candidates


def _records(query: str, corpus: str = "openalex", n: int = 6) -> list[PaperMetadata]:
    return [
        PaperMetadata(
            title=f"Paper {corpus}:{query} #{i}",
            abstract="A" * 300,
            doi=f"10.{hash(query) % 10**6}.{corpus}.{i}",
            provider_id=f"W{abs(hash(query)) % 10**6}.{corpus}.{i}",
            source_provider=corpus,
            citation_count=100 - i,
        )
        for i in range(n)
    ]


class _CountingProvider:
    """Returns deterministic records and counts every search call."""

    def __init__(self, corpus: str = "openalex") -> None:
        self.calls = 0
        self.corpus = corpus

    async def search(self, query: str, *, limit: int = 10) -> list[PaperMetadata]:
        self.calls += 1
        return _records(query, corpus=self.corpus)


def _making_spy() -> "dict":
    return {"calls": 0}


class TestDistinctQueryReduction:
    def test_frame_references_only_the_30_pool_queries(self):
        pool = s.load_pool()
        frame = s.build_frame(pool)
        assert len(frame) == s.N_FRAME
        queries = _queries_in(frame)
        assert len(queries) <= len(pool)
        assert set(queries) == {d["query"] for d in pool}
        # the optimization premise: 96 pairs but only 30 distinct fetch targets
        assert len(queries) == 30

    async def test_fetch_requests_each_distinct_query_exactly_once(self, tmp_path):
        provider = _CountingProvider()
        frame = s.build_frame(s.load_pool())
        cache = await b._fetch_screening_queries(
            frame, provider, tmp_path / "corpus_query_cache.json", "h", s.SEED, report_progress=False
        )
        assert provider.calls == 30
        assert set(cache["records"]) == set(_queries_in(frame))

    async def test_screening_is_pure_compute_with_zero_provider_calls(self, tmp_path):
        provider = _CountingProvider()
        frame = s.build_frame(s.load_pool())
        cache = await b._fetch_screening_queries(
            frame, provider, tmp_path / "corpus_query_cache.json", "h", s.SEED, report_progress=False
        )
        before = provider.calls
        _screen_candidates(frame, cache, report_progress=False)
        assert provider.calls == before  # screening touches no network/provider


def _semantic(records: list[dict]) -> list[tuple]:
    # Timestamps/elapsed are observability fields; compare screening semantics.
    return [
        tuple((r["candidate_id"], r["decision"], r["usable_a"], r["usable_b"], r["reason"],
               tuple(r["sample_ids_a"]), tuple(r["sample_ids_b"])))
        for r in records
    ]


def _decision(ua: int, ub: int) -> tuple[str, str]:
    if ua >= s.IN_T and ub >= s.IN_T:
        return "eligible", "IN1"
    if ua < s.IN_T and ub < s.IN_T:
        return "excluded", f"EX1 insufficient_evidence_both ({ua}/{ub})"
    if ua < s.IN_T:
        return "excluded", f"EX1 insufficient_evidence_side_a={ua}"
    return "excluded", f"EX1 insufficient_evidence_side_b={ub}"


async def _legacy_per_candidate_screen(frame, provider) -> list[tuple]:
    """Reference: the pre-optimization architecture (2 searches per candidate)."""
    out: list[tuple] = []
    for c in frame:
        ra = await provider.search(c["query_a"])
        rb = await provider.search(c["query_b"])
        ua = [b._paper_from_meta(p, "openalex") for p in ra]
        ub = [b._paper_from_meta(p, "openalex") for p in rb]
        ua = [p for p in ua if p is not None]
        ub = [p for p in ub if p is not None]
        decision, reason = _decision(len(ua), len(ub))
        out.append((c["candidate_id"], decision, len(ua), len(ub), reason,
                    tuple([p.paper_id for p in ua[:5]]), tuple([p.paper_id for p in ub[:5]])))
    return out


class TestDecisionEquivalence:
    async def test_query_cache_screen_matches_legacy_per_candidate_screen(self, tmp_path):
        """For identical mocked corpus results, cached screening decisions are
        indistinguishable from the 2-search-per-candidate architecture."""
        frame = s.build_frame(s.load_pool())
        legacy = await _legacy_per_candidate_screen(frame, _CountingProvider())

        cache = await b._fetch_screening_queries(
            frame, _CountingProvider(), tmp_path / "corpus_query_cache.json", "h", s.SEED, report_progress=False
        )
        optimized = _screen_candidates(frame, cache, report_progress=False)
        assert _semantic(optimized) == legacy


class TestBuildReusesCache:
    async def test_build_side_zero_openalex_calls_from_cache(self, tmp_path):
        frame = s.build_frame(s.load_pool())
        cache = await b._fetch_screening_queries(
            frame, _CountingProvider(), tmp_path / "corpus_query_cache.json", "h", s.SEED, report_progress=False
        )
        spy = _making_spy()

        class _OpenAlexSpy:
            def __init__(self, spy_: dict) -> None:
                self._s = spy_

            async def search(self, *_a, **_k):
                self._s["calls"] += 1
                raise AssertionError("build must reuse cached records, not re-query OpenAlex")

        provider = {
            "openalex": _OpenAlexSpy(spy),
            "pubmed": _CountingProvider("pubmed"),
            "arxiv": _CountingProvider("arxiv"),
        }
        stats: dict = {}
        side = await b._build_side(
            frame[0]["query_a"], provider, stats,
            {"openalex": True, "pubmed": True, "arxiv": True}, cache,
        )
        assert spy["calls"] == 0  # the OpenAlex spy was never touched
        assert any(p.source_provider == "openalex" for p in side)
        assert any(p.source_provider == "pubmed" for p in side)
        assert any(p.source_provider == "arxiv" for p in side)
        oa_records = {r["provider_id"] for r in cache["records"][frame[0]["query_a"]]}
        assert {p.paper_id for p in side if p.source_provider == "openalex"} == oa_records

    async def test_cache_split_across_two_runs_is_equivalent(self, tmp_path):
        """Deterministic local checkpointing must not change decisions: whether the
        cache is populated in one run or resumed from a partial one, screening is
        identical (query results are cached per query, deduplicated implicitly)."""
        frame = s.build_frame(s.load_pool())
        cache_path = tmp_path / "corpus_query_cache.json"
        queries = _queries_in(frame)
        provider = _CountingProvider()
        await b._fetch_screening_queries(
            frame, provider, cache_path, "h", s.SEED, report_progress=False
        )
        one_shot = _screen_candidates(frame, b._load_cache(cache_path, "h", s.SEED), report_progress=False)

        # resume: wipe half the cache, refetch only the other half
        partial = b._load_cache(cache_path, "h", s.SEED)
        partial["records"] = {q: partial["records"][q] for q in queries[:15]}
        b._save_cache(cache_path, partial)
        provider.calls = 0
        await b._fetch_screening_queries(frame, provider, cache_path, "h", s.SEED, report_progress=False)
        assert provider.calls == 15  # only the missing queries are fetched
        resumed = _screen_candidates(frame, b._load_cache(cache_path, "h", s.SEED), report_progress=False)
        assert _semantic(resumed) == _semantic(one_shot)


class TestCacheKeyScoping:
    def test_cache_invalidated_when_pool_or_seed_changes(self, tmp_path):
        cache_path = tmp_path / "corpus_query_cache.json"
        payload = {
            "kind": "openalex_query_cache",
            "pool_sha256": "poolA", "seed": 1, "cached_utc": "now",
            "records": {"q1": [{"title": "x", "provider_id": "W1", "citation_count": 0}]},
        }
        cache_path.write_text(json.dumps(payload), encoding="utf-8")
        # same key -> reused
        assert b._load_cache(cache_path, "poolA", 1)["records"] == payload["records"]
        # different pool or seed -> treated as empty (refetch required)
        assert b._load_cache(cache_path, "poolB", 1)["records"] == {}
        assert b._load_cache(cache_path, "poolA", 2)["records"] == {}
        # invalid kind or corrupt file -> safe empty cache
        corrupt = tmp_path / "corrupt.json"
        corrupt.write_text("{not json", encoding="utf-8")
        assert b._load_cache(corrupt, "poolA", 1)["records"] == {}

    async def test_full_build_reuses_cache_after_screening(self, tmp_path, monkeypatch):
        """End-to-end (all corpora mocked): OpenAlex is queried exactly 30 times
        at the fetch phase and zero times during the build phase."""
        import app.providers.literature.arxiv as arxiv_mod
        import app.providers.literature.openalex as oa_mod
        import app.providers.literature.pubmed as pm_mod

        oa_provider = _CountingProvider("openalex")
        pm_provider = _CountingProvider("pubmed")
        ax_provider = _CountingProvider("arxiv")
        monkeypatch.setattr(oa_mod, "OpenAlexProvider", lambda *a, **k: oa_provider)
        monkeypatch.setattr(pm_mod, "PubmedProvider", lambda *a, **k: pm_provider)
        monkeypatch.setattr(arxiv_mod, "ArxivProvider", lambda *a, **k: ax_provider)

        result = await b.build(tmp_path, screen_only=False)
        assert result["n_cases"] == s.N_TARGET
        # fetch phase only: 30 distinct queries, exactly once
        assert oa_provider.calls == 30
        # build reused the cache: openalex provider was not re-queried for records
        assert oa_provider.calls == 30
        manifest = json.loads((tmp_path / "sampling_manifest.json").read_text(encoding="utf-8"))
        opt = manifest["request_optimization"]
        assert opt["optimized_openalex_search_calls"]["total"] == 30
        assert opt["naive_openalex_search_calls"]["total"] == (2 * s.N_FRAME) + (2 * s.N_TARGET)
        assert (tmp_path / "corpus_query_cache.json").exists()
        assert (tmp_path / "candidate_population.json").exists()
        # population records derive purely from the cache: no EX2 path exists at screen time
        pop = json.loads((tmp_path / "candidate_population.json").read_text(encoding="utf-8"))["candidates"]
        assert len(pop) == s.N_FRAME
        assert all(r["decision"] in ("eligible", "excluded") for r in pop)
        assert not any(r["decision"] == "excluded_provider" for r in pop)