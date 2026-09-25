"""Offline tests for the 429/retry + query-cache hardening (no live corpus requests).

Locks in (query-fetch architecture): 429 is never an empty result, never EX1,
never a valid exclusion; server Retry-After is respected; hard cooldowns and
persistent provider failures abort the fetch phase cleanly, preserving the
partial cache checkpoint and leaving no decision artifacts; screening itself is
pure computation so it can never mask a provider failure as an exclusion.
"""
from __future__ import annotations

import json

import pytest

from app.core.exceptions import ProviderError, ProviderThrottledError
from app.providers.literature.base import PaperMetadata
from evaluation.datav2.build import (
    HARD_COOLDOWN_THRESHOLD,
    TRANSIENT_MAX_WAIT,
    CorpusCooldownError,
    _OpenAlexWithRetry,
    _fetch_screening_queries,
    _screen_candidates,
)


def _records(query: str, n: int = 6) -> list[PaperMetadata]:
    return [
        PaperMetadata(
            title=f"Paper {query} #{i}",
            abstract="A" * 400,
            doi=f"10.1000/{_safe(query)}.{i}",
            provider_id=f"W{abs(hash(query)) % 10**6}.{i}",
            source_provider="openalex",
            citation_count=100 - i,
        )
        for i in range(n)
    ]


def _safe(query: str) -> str:
    return "".join(ch for ch in query if ch.isalnum())[:20]


class _FakeProvider:
    """Deterministic fake: ok | provider_error | throttle_long | throttle_once_ok.
    ``fail_on_call`` raises a persistent ProviderError on that exact call."""

    mode = "ok"
    calls = 0
    fail_on_call: int | None = None

    async def search(self, query: str, *, limit: int = 10) -> list[PaperMetadata] | None:
        self.calls += 1
        if self.fail_on_call is not None and self.calls == self.fail_on_call:
            raise ProviderError("OpenAlex search failed: 503")
        if self.mode == "provider_error":
            raise ProviderError("OpenAlex search failed: 503")
        if self.mode == "throttle_long":
            raise ProviderThrottledError("429", retry_after=999999, provider="openalex")
        if self.mode == "throttle_once_ok":
            if self.calls == 1:
                raise ProviderThrottledError("429", retry_after=2, provider="openalex")
            return _records(query)
        return _records(query)


def _mini_frame() -> list[dict]:
    return [
        {
            "candidate_id": "cand_000",
            "pair_id": "v2_a_b",
            "group": "inter_cs_ai_quant_methods",
            "domain_a": "a",
            "domain_b": "b",
            "query_a": "alpha",
            "query_b": "beta",
        },
        {
            "candidate_id": "cand_001",
            "pair_id": "v2_c_d",
            "group": "intra_life_health",
            "domain_a": "c",
            "domain_b": "d",
            "query_a": "gamma",
            "query_b": "delta",
        },
    ]


def _cache_key(pool_sha256: str = "h1", seed: int = 20260925) -> dict:
    return {"kind": "openalex_query_cache", "pool_sha256": pool_sha256, "seed": seed, "cached_utc": None, "records": {}}


class Test429IsNotAnEmptyResult:
    async def test_hard_cooldown_raises_not_empty_list(self):
        rw = _OpenAlexWithRetry(_FakeProvider())
        rw.provider.mode = "throttle_long"
        with pytest.raises(CorpusCooldownError):
            await rw.search("anything")

    async def test_ok_provider_returns_records(self):
        rw = _OpenAlexWithRetry(_FakeProvider())
        out = await rw.search("anything")
        assert len(out) == 6

    def test_throttled_is_distinct_error_type(self):
        assert issubclass(ProviderThrottledError, ProviderError)
        assert issubclass(CorpusCooldownError, RuntimeError)


class TestRetryAfterRespected:
    async def test_transient_retry_after_is_used(self, monkeypatch):
        provider = _FakeProvider()
        provider.mode = "throttle_once_ok"
        rw = _OpenAlexWithRetry(provider)
        sleeps: list[float] = []

        async def _sleep(secs: float) -> None:
            sleeps.append(secs)

        monkeypatch.setattr("evaluation.datav2.build.asyncio.sleep", _sleep)
        out = await rw.search("anything")
        assert len(out) == 6
        # First call was throttled with Retry-After=2 -> the wrapper must wait 2s
        # (bounded by TRANSIENT_MAX_WAIT), *not* the 3/9/27 backoff sequence.
        assert sleeps == [2]
        assert rw.throttle_hits == 1
        assert rw.calls == 1  # one wrapper-level search
        assert provider.calls == 2  # throttled once, then ok

    def test_tolerance_window_bounds_transient_wait(self):
        assert TRANSIENT_MAX_WAIT >= 1
        assert HARD_COOLDOWN_THRESHOLD > TRANSIENT_MAX_WAIT


class TestProviderFailureCannotBecomeExclusion:
    async def test_persistent_provider_error_aborts_fetch_never_becomes_decision(self, tmp_path):
        """A provider access failure must abort the fetch phase — it can never
        yield an 'excluded' (EX1) or 'eligible' (IN1) decision record."""
        provider = _FakeProvider()
        provider.mode = "provider_error"
        cache_path = tmp_path / "corpus_query_cache.json"
        with pytest.raises(ProviderError):
            await _fetch_screening_queries(
                _mini_frame(), provider, cache_path, "h1", 20260925, report_progress=False
            )
        # No records may be recorded from a failed access; the cache (if written)
        # must be empty so a resume refetches everything rather than scoring zeros.
        cached = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
        assert cached.get("records", {}) == {}
        # Structural guarantee: _screen_candidates only accepts a cache dict and
        # never touches a provider, so a failure can never leak into a decision.

    async def test_long_cooldown_aborts_fetch_instead_of_excluding(self, tmp_path):
        provider = _OpenAlexWithRetry(_FakeProvider())
        provider.provider.mode = "throttle_long"
        with pytest.raises(CorpusCooldownError):
            await _fetch_screening_queries(
                _mini_frame(), provider, tmp_path / "corpus_query_cache.json", "h1", 20260925, report_progress=False
            )


class TestCheckpointPreservation:
    async def test_interrupted_screening_keeps_frame_and_never_writes_population(self, tmp_path):
        frame = _mini_frame()
        frame_file = tmp_path / "candidate_frame.json"
        payload = {"seed": 20260925, "candidates": frame}
        frame_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        before = frame_file.read_bytes()

        provider = _FakeProvider()
        provider.fail_on_call = 2  # alpha cached, beta aborts the fetch phase
        with pytest.raises(ProviderError):
            await _fetch_screening_queries(
                frame, provider, tmp_path / "corpus_query_cache.json", "h1", 20260925, report_progress=False
            )
        # frame untouched; no partial population artifact, no dataset, no EX2 row.
        assert frame_file.read_bytes() == before
        assert not (tmp_path / "candidate_population.json").exists()
        assert not (tmp_path / "dataset_v2.json").exists()
        assert (tmp_path / "corpus_query_cache.json").exists()

    async def test_interrupt_and_resume_fetches_only_remaining_queries(self, tmp_path):
        cache_path = tmp_path / "corpus_query_cache.json"
        provider = _FakeProvider()
        provider.fail_on_call = 3  # alpha,gamma cached (frame query order); beta aborts

        # _queries_in() de-duplicates in (query_a..., query_b...) order, so for the
        # mini frame the fetch order is alpha, gamma, beta, delta.
        with pytest.raises(ProviderError):
            await _fetch_screening_queries(
                _mini_frame(), provider, cache_path, "h1", 20260925, report_progress=False
            )
        cached = json.loads(cache_path.read_text(encoding="utf-8"))
        assert set(cached["records"]) == {"alpha", "gamma"}
        assert cached["pool_sha256"] == "h1"
        assert cached["seed"] == 20260925

        provider.calls = 0
        provider.fail_on_call = None
        out = await _fetch_screening_queries(
            _mini_frame(), provider, cache_path, "h1", 20260925, report_progress=False
        )
        assert provider.calls == 2  # only the two remaining queries
        assert set(out["records"]) == {"alpha", "beta", "gamma", "delta"}


class TestProgressIsSideEffectOnly:
    @staticmethod
    def _semantic(records: list[dict]) -> list[tuple]:
        # Timestamps/elapsed are observability fields; compare the screening
        # semantics (decisions, usable counts, reasons, sample ids) only.
        return [
            tuple((r["candidate_id"], r["decision"], r["usable_a"], r["usable_b"], r["reason"], tuple(r["sample_ids_a"]), tuple(r["sample_ids_b"])))
            for r in records
        ]

    async def test_progress_does_not_change_results(self, tmp_path, capsys):
        cache = await _fetch_screening_queries(
            _mini_frame(), _FakeProvider(), tmp_path / "corpus_query_cache.json", "h1", 20260925, report_progress=False
        )
        with_progress = _screen_candidates(_mini_frame(), cache, report_progress=True)
        out = capsys.readouterr().out
        assert "eligible=" in out
        assert "provider_fail=0" in out
        assert "2/2 done" in out

        without_progress = _screen_candidates(_mini_frame(), cache, report_progress=False)
        assert self._semantic(without_progress) == self._semantic(with_progress)