"""v2 dataset builder (Phase 3): sampling + multi-corpus retrieval + artifacts.

Implements the frozen CASE_SAMPLING_PROTOCOL.md. Pipeline:

1. load frozen domain pool -> deterministic stratified candidate frame (§6)
2. eligibility screening via OpenAlex (§7)     -> candidate_population.json
3. seeded stratified final sample (§9)          -> selected case ids
4. multi-corpus build per selected case (§3, 3E): OpenAlex (always),
   PubMed (biomed domains), arXiv (best-effort); deterministic dedup (§10)
5. write datasets/v2 artifacts + v1 read-only snapshot (§3I)

Run:  python -m evaluation.datav2.build [--root datasets/v2]
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import random
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evaluation.build_real_dataset import (
    _expected_evidence,
    _paper_from_meta,
    _top_topics,
)
from app.core.exceptions import ProviderError, ProviderThrottledError
from app.providers.literature.base import PaperMetadata
from evaluation.datav2 import sampling as s
from evaluation.schemas import EvaluationCase, EvaluationDataset, ResearcherInput

ROOT = Path(__file__).resolve().parents[2] / "datasets" / "v2"
DATA = Path(__file__).resolve().parents[1] / "data"
PROTOCOL = Path(__file__).resolve().parents[2] / "CASE_SAMPLING_PROTOCOL.md"

SEARCH_LIMIT = 10
PER_SIDE = 5
MIN_PER_SIDE_AFTER_DEDUP = 3
OPENALEX_CONCURRENCY = 2
OPENALEX_MIN_DELAY = 0.35
PROGRESS_EVERY = 8  # screening progress ~every 8 candidates (observability only)

# 429 handling: a server-supplied Retry-After above this threshold means the
# provider requires a long cooldown -> abort cleanly (never retry-burn, never an
# empty result, never an exclusion). Below it we pause and retry, bounded.
HARD_COOLDOWN_THRESHOLD = 300
TRANSIENT_MAX_WAIT = 120


class CorpusCooldownError(RuntimeError):
    """Provider returned 429 with a long Retry-After; screening must abort."""
    def __init__(self, provider: str = "openalex", retry_after: int | None = None, detail: str = "") -> None:
        self.provider = provider
        self.retry_after = retry_after
        self.detail = detail
        super().__init__(
            f"{provider} requires an API cooldown (Retry-After={retry_after}s, "
            f"threshold={HARD_COOLDOWN_THRESHOLD}s) [query={detail[:80]}]"
        )

CORPUS_ORDER = ("openalex", "pubmed", "arxiv")
PROVIDER_PRIORITY = {"openalex": 0, "pubmed": 1, "arxiv": 2}

# v1 case -> pool domain pair that corresponds to it (mapping, not a requirement).
V1_PAIR_CANDIDATES: dict[str, tuple[str, str] | None] = {
    "federated_learning_x_privacy": ("federated_learning", "differential_privacy"),
    "causal_inference_x_clinical_ml": ("causal_inference", "clinical_decision_support"),
    "gnn_x_protein_structure": ("graph_neural_networks", "protein_structure_prediction"),
    "recommender_x_fairness": ("recommender_systems", "algorithmic_fairness"),
    "rl_x_sim_to_real": None,
    "clinical_nlp_x_ehr": None,
    "climate_downscaling_x_deep_learning": None,
    "quantum_chemistry_x_dft": None,
    "single_cell_x_transfer_learning": None,
    "knowledge_graph_x_question_answering": None,
    "speech_recognition_x_hearing_aids": None,
    "materials_discovery_x_active_learning": None,
}


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _norm_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (title or "").lower())


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )


class _OpenAlexWithRetry:
    def __init__(self, provider) -> None:
        self.provider = provider
        self.errors: list[dict[str, Any]] = []
        self.calls = 0
        self.throttle_hits = 0

    async def search(self, query: str, *, limit: int = SEARCH_LIMIT) -> list[Any]:
        """Retry wrapper honoring provider throttling.

        HTTP 429 semantics (never an empty result, never an exclusion):
        * server-supplied ``Retry-After`` > HARD_COOLDOWN_THRESHOLD  -> raise
          ``CorpusCooldownError`` so screening aborts cleanly instead of burning
          the normal backoff sequence against a known hard rate limit.
        * otherwise pause for ``Retry-After`` (bounded) and retry.
        * non-throttle errors (5xx/network) retry with the normal backoff.
        """
        self.calls += 1
        last: Exception | None = None
        for attempt in range(1, 5):
            try:
                return await self.provider.search(query, limit=limit)
            except ProviderThrottledError as exc:
                self.throttle_hits += 1
                retry_after = exc.retry_after
                if retry_after is not None and retry_after > HARD_COOLDOWN_THRESHOLD:
                    raise CorpusCooldownError(
                        provider=exc.provider or "openalex",
                        retry_after=retry_after,
                        detail=query,
                    ) from exc
                wait = min(retry_after, TRANSIENT_MAX_WAIT) if retry_after is not None else (
                    (2 ** attempt) * random.uniform(0.8, 1.2)
                )
                print(f"[screen] throttled (429, retry-after={retry_after}) — pausing {wait:.0f}s", flush=True)
                await asyncio.sleep(wait)
            except Exception as exc:  # non-429 provider/network errors
                last = exc
                if attempt < 4:
                    await asyncio.sleep((3 ** attempt) * random.uniform(0.8, 1.2))
        # Persistent failure: surface loudly; the caller aborts the fetch phase
        # (provider-unavailable) instead of misreading it as 'no records'.
        self.errors.append({"query": query, "error": str(last)[:300]})
        raise ProviderError(f"OpenAlex screening failed after 4 attempts: {last}") from last


def _queries_in(frame: list[dict[str, Any]]) -> list[str]:
    """The distinct OpenAlex query strings used by the frame (one per domain).

    The 96-pair frame repeats each domain query across many candidate slots, so
    there are at most one query per pool domain (30) — not 192 fetch targets.
    """
    return list(dict.fromkeys([c["query_a"] for c in frame] + [c["query_b"] for c in frame]))


def _record_to_meta(rec: dict[str, Any]) -> Any:
    """Rehydrate a cached OpenAlex record dict into a PaperMetadata."""
    return PaperMetadata(
        title=rec.get("title") or "Untitled",
        abstract=rec.get("abstract"),
        authors=list(rec.get("authors") or []),
        year=rec.get("year"),
        doi=rec.get("doi"),
        venue=rec.get("venue"),
        source_provider=rec.get("source_provider") or "openalex",
        provider_id=rec.get("provider_id") or "",
        source_url=rec.get("source_url"),
        citation_count=rec.get("citation_count") or 0,
        topics=list(rec.get("topics") or []),
    )


def _paper_metadata_to_record(meta) -> dict[str, Any]:
    """Serialize a PaperMetadata for the per-query OpenAlex cache."""
    return {
        "title": meta.title,
        "abstract": meta.abstract,
        "authors": list(meta.authors),
        "year": meta.year,
        "doi": meta.doi,
        "venue": meta.venue,
        "source_provider": meta.source_provider,
        "provider_id": meta.provider_id,
        "source_url": meta.source_url,
        "citation_count": meta.citation_count,
        "topics": list(meta.topics),
    }


def _save_cache(cache_path: Path, cache: dict[str, Any]) -> None:
    _write_json(cache_path, cache)


def _load_cache(cache_path: Path, pool_sha256: str, seed: int) -> dict[str, Any]:
    """Return a valid per-query cache (keyed to pool+seed) or an empty one."""
    fresh = {"kind": "openalex_query_cache", "pool_sha256": pool_sha256, "seed": seed, "cached_utc": None, "records": {}}
    if not cache_path.exists():
        return fresh
    try:
        c = json.loads(cache_path.read_text(encoding="utf-8"))
    except Exception:
        return fresh
    if not (isinstance(c, dict) and c.get("kind") == "openalex_query_cache"):
        return fresh
    if c.get("pool_sha256") != pool_sha256 or c.get("seed") != seed:
        return fresh  # stale key -> refetch everything
    c.setdefault("records", {})
    return c


async def _fetch_screening_queries(
    frame: list[dict[str, Any]],
    provider,
    cache_path: Path,
    pool_sha256: str,
    seed: int,
    *,
    report_progress: bool = True,
) -> dict[str, Any]:
    """Fetch each distinct OpenAlex query exactly once, checkpointing to disk.

    Raises CorpusCooldownError (hard throttle) or ProviderError (persistent
    provider-access failure) -> the caller aborts cleanly and the cache keeps
    every query already fetched, so a later run resumes with zero repeats.
    """
    queries = _queries_in(frame)
    cache = _load_cache(cache_path, pool_sha256, seed)
    missing = [q for q in queries if q not in cache["records"]]
    t0 = time.perf_counter()
    for i, q in enumerate(missing, 1):
        try:
            metas = await provider.search(q, limit=SEARCH_LIMIT)
        except CorpusCooldownError:
            _save_cache(cache_path, cache)
            raise
        except Exception as exc:
            _save_cache(cache_path, cache)
            raise ProviderError(f"OpenAlex query fetch failed persistently: {q!r}: {str(exc)[:200]}") from exc
        fetched_utc = _utcnow()
        cache["records"][q] = [
            {**_paper_metadata_to_record(m), "retrieved_utc": fetched_utc}
            for m in metas
        ]
        cache["cached_utc"] = fetched_utc
        _save_cache(cache_path, cache)  # incremental checkpoint (resume-safe)
        if i < len(missing):
            await asyncio.sleep(OPENALEX_MIN_DELAY)  # polite pacing between queries
        if report_progress and (i % 5 == 0 or i == len(missing)):
            print(
                f"[screen] queries cached {i}/{len(missing)} (of {len(queries)} distinct) | "
                f"elapsed={round(time.perf_counter() - t0, 1)}s",
                flush=True,
            )
    return cache


def _screen_candidates(
    frame: list[dict[str, Any]],
    cache: dict[str, Any],
    *,
    report_progress: bool = True,
) -> list[dict[str, Any]]:
    """Deterministic eligibility screening over cached per-query results.

    Purely local (no network): usable counts per side come from the per-domain
    query cache, so a candidate's decision is EXACTLY what a per-query fetch
    would produce. Provider failures can never appear here — they abort the
    fetch phase instead (no EX2, no EX1-from-failure).
    """
    t_start = time.perf_counter()

    def _decision(cand: dict[str, Any], usable_a: int, usable_b: int) -> tuple[str, str]:
        if usable_a >= s.IN_T and usable_b >= s.IN_T:
            return "eligible", "IN1"
        if usable_a < s.IN_T and usable_b < s.IN_T:
            return "excluded", f"EX1 insufficient_evidence_both ({usable_a}/{usable_b})"
        if usable_a < s.IN_T:
            return "excluded", f"EX1 insufficient_evidence_side_a={usable_a}"
        return "excluded", f"EX1 insufficient_evidence_side_b={usable_b}"

    screened: list[dict[str, Any]] = []
    for i, cand in enumerate(frame, 1):
        t0 = time.perf_counter()
        ua = [
            p
            for m in (_record_to_meta(d) for d in cache["records"][cand["query_a"]])
            for p in [_paper_from_meta(m, "openalex")]
            if p is not None
        ]
        ub = [
            p
            for m in (_record_to_meta(d) for d in cache["records"][cand["query_b"]])
            for p in [_paper_from_meta(m, "openalex")]
            if p is not None
        ]
        decision, reason = _decision(cand, len(ua), len(ub))
        screened.append(
            {
                "candidate_id": cand["candidate_id"],
                "pair_id": cand["pair_id"],
                "group": cand["group"],
                "domain_a": cand["domain_a"],
                "domain_b": cand["domain_b"],
                "query_a": cand["query_a"],
                "query_b": cand["query_b"],
                "usable_a": len(ua),
                "usable_b": len(ub),
                "decision": decision,
                "reason": reason,
                "sample_ids_a": [p.paper_id for p in ua[:5]],
                "sample_ids_b": [p.paper_id for p in ub[:5]],
                "screened_utc": _utcnow(),
                "seconds": round(time.perf_counter() - t0, 2),
            }
        )
        if report_progress and (i % PROGRESS_EVERY == 0 or i == len(frame)):
            counts = [r["decision"] for r in screened]
            print(
                f"[screen] {i}/{len(frame)} done | eligible={counts.count('eligible')} "
                f"excluded={counts.count('excluded')} provider_fail=0 | "
                f"elapsed={round(time.perf_counter() - t_start, 1)}s",
                flush=True,
            )
    return screened


def _dedup_side(
    records: list[Any],
    audit: list[dict[str, Any]],
    case_key: str,
    side: str,
) -> list[Any]:
    """Deterministic dedup (protocol §10): keep first in (provider priority, citations)."""
    ordered = sorted(
        records,
        key=lambda r: (PROVIDER_PRIORITY.get(r.source_provider, 9), -(r.citation_count or 0), r.paper_id),
    )
    kept: list[Any] = []
    for rec in ordered:
        match, matcher = _find_dup(rec, kept, warn_fallback=side)
        audit.append(
            {
                "case": case_key,
                "side": side,
                "record": rec.paper_id,
                "corpus": rec.source_provider,
                "title": rec.title,
                "doi": rec.doi,
                "kept": matcher is None,
                "matcher": matcher,
                "dropped_by": match,
            }
        )
        if matcher is None:
            kept.append(rec)
    return kept


def _find_dup(rec, kept: list[Any], warn_fallback: str) -> tuple[str | None, str | None]:
    doi = (rec.doi or "").lower()
    ntitle = _norm_title(rec.title)
    for k in kept:
        kdoi = (k.doi or "").lower()
        if doi and kdoi and doi == kdoi:
            return k.paper_id, "doi"
        if ntitle and _norm_title(k.title) == ntitle and rec.year and k.year and rec.year == k.year:
            return k.paper_id, "norm_title+year"
        if (k.source_provider == rec.source_provider) and k.provider_id and rec.provider_id and k.provider_id == rec.provider_id:
            return k.paper_id, "provider_id"
        if ntitle and _norm_title(k.title) == ntitle:
            return k.paper_id, f"norm_title_only_fallback({warn_fallback})"
    return None, None


async def _build_side(
    query: str,
    provider: dict[str, Any],
    stats: dict[str, Any],
    applicable: dict[str, bool],
    openalex_cache: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Retrieve records for one case side from all applicable corpora.

    OpenAlex responses are REUSED from the screening cache (same domain query,
    same session) — the build makes zero additional OpenAlex requests. PubMed
    and arXiv are queried live (best-effort for arXiv).
    """
    out: list[Any] = []
    for corpus in CORPUS_ORDER:
        if not applicable[corpus]:
            continue
        try:
            retrieved_map: dict[str, str | None] = {}
            if corpus == "openalex":
                assert openalex_cache is not None and query in openalex_cache["records"]
                recs = openalex_cache["records"][query]
                metas = [_record_to_meta(d) for d in recs]
                retrieved_map = {d.get("provider_id") or d.get("doi"): d.get("retrieved_utc") for d in recs}
            elif corpus == "pubmed":
                metas = await asyncio.wait_for(provider["pubmed"].search(query, limit=SEARCH_LIMIT), timeout=60)
            else:
                metas = await asyncio.wait_for(provider["arxiv"].search(query, limit=SEARCH_LIMIT), timeout=30)
            stats.setdefault("calls", {}).setdefault(corpus, []).append(query)
            for m in metas:
                paper = _paper_from_meta(m, corpus)
                if paper is not None:
                    paper.retrieved_utc = retrieved_map.get(m.provider_id or m.doi) or _utcnow()
                    out.append(paper)
        except Exception as exc:  # arXiv best-effort; others fail loudly via empty
            stats.setdefault("corpus_errors", []).append(
                {"corpus": corpus, "query": query, "error": f"{type(exc).__name__}: {str(exc)[:200]}"}
            )
            if corpus in ("openalex", "pubmed"):
                raise
    return out


def _applicable(pool: list[dict[str, Any]], a_id: str, b_id: str) -> dict[str, bool]:
    da = next(d for d in pool if d["id"] == a_id)
    db = next(d for d in pool if d["id"] == b_id)
    return {
        "openalex": True,
        "pubmed": bool(da["biomed"] or db["biomed"]),
        "arxiv": True,
    }


async def _probe_arxiv(provider) -> tuple[bool, str | None]:
    """Best-effort probe; a failing arXiv never blocks the build (protocol §8)."""
    try:
        await asyncio.wait_for(
            provider.search("protein structure prediction", limit=1), timeout=25
        )
        return True, None
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {str(exc)[:200]}"


def _select_side(kept: list[Any], side_slots: int = PER_SIDE) -> list[Any]:
    """Per-side record selection that guarantees corpus mixture.

    OpenAlex (primary) claims up to 3 slots; each other corpus that returned
    records claims up to 1 slot; remaining slots are filled from the pooled
    remainder. Within a corpus, records are ranked by (-citation_count, id).
    This keeps corpus provenance explicit (protocol 3E) instead of letting
    OpenAlex citation counts crowd out every other corpus.
    """
    slots = {"openalex": min(3, side_slots - 1), "pubmed": 1, "arxiv": 1}
    if side_slots < 2:  # degenerate case handled below
        slots = {"openalex": side_slots, "pubmed": 0, "arxiv": 0}
    by_corpus: dict[str, list[Any]] = {}
    for r in kept:
        by_corpus.setdefault(r.source_provider, []).append(r)
    for c in by_corpus:
        by_corpus[c].sort(key=lambda r: (-(r.citation_count or 0), r.paper_id))
    chosen: list[Any] = []
    for c in ("openalex", "pubmed", "arxiv"):
        if c in by_corpus:
            chosen.extend(by_corpus[c][: slots.get(c, 0)])
    used_ids = {r.paper_id for r in chosen}
    filled = len(chosen)
    if filled < side_slots:
        remainder = [
            r
            for c in by_corpus
            for r in by_corpus[c]
            if r.paper_id not in used_ids
        ]
        remainder.sort(key=lambda r: (-(r.citation_count or 0), r.paper_id))
        for r in remainder[: side_slots - filled]:
            chosen.append(r)
    chosen.sort(key=lambda r: (-(r.citation_count or 0), r.paper_id))
    return chosen[:side_slots]


async def _build_case(
    pair: dict[str, Any],
    pool: list[dict[str, Any]],
    provider: dict[str, Any],
    stats: dict[str, Any],
    selection_utc: str,
    openalex_cache: dict[str, Any] | None = None,
) -> EvaluationCase:
    applicable = _applicable(pool, pair["domain_a"], pair["domain_b"])
    if not stats.get("arxiv_ok", True):
        applicable["arxiv"] = False
    a_records = await _build_side(pair["query_a"], provider, stats, applicable, openalex_cache)
    b_records = await _build_side(pair["query_b"], provider, stats, applicable, openalex_cache)
    audit = stats.setdefault("dedup_audit", [])
    a_kept = _dedup_side(a_records, audit, pair["pair_id"], "a")
    b_kept = _dedup_side(b_records, audit, pair["pair_id"], "b")
    if len(a_kept) < MIN_PER_SIDE_AFTER_DEDUP or len(b_kept) < MIN_PER_SIDE_AFTER_DEDUP:
        raise ValueError(
            f"{pair['pair_id']}: side a={len(a_kept)} (<{MIN_PER_SIDE_AFTER_DEDUP}) or b={len(b_kept)} after dedup"
        )
    a_kept.sort(key=lambda p: (-(p.citation_count or 0), p.paper_id))
    b_kept.sort(key=lambda p: (-(p.citation_count or 0), p.paper_id))
    a_kept, b_kept = _select_side(a_kept), _select_side(b_kept)

    ra = next(d for d in pool if d["id"] == pair["domain_a"])
    rb = next(d for d in pool if d["id"] == pair["domain_b"])
    a = ResearcherInput(
        name=ra["name"],
        bio=f"Illustrative research-domain persona for '{ra['name']}' (built from the frozen v2 domain pool; not a real individual).",
        topics=_top_topics(a_kept, 6),
        methods=[],
        domains=[ra["name"]],
    )
    b = ResearcherInput(
        name=rb["name"],
        bio=f"Illustrative research-domain persona for '{rb['name']}' (built from the frozen v2 domain pool; not a real individual).",
        topics=_top_topics(b_kept, 6),
        methods=[],
        domains=[rb["name"]],
    )
    all_papers = a_kept + b_kept
    return EvaluationCase(
        case_id=pair["pair_id"],
        label=f"v2 case: {ra['name']} × {rb['name']}",
        evaluation_question=(
            f"Which real, evidence-grounded research direction plausibly connects "
            f"{ra['name']} with {rb['name']}?"
        ),
        researcher_a=a,
        researcher_b=b,
        field_query=pair["field_query"],
        source_papers=all_papers,
        expected_topics=_top_topics(all_papers, 12),
        expected_methods=[],
        expected_gaps=[],
        expected_evidence_references=_expected_evidence(all_papers, k=3),
        expected_evidence_source="machine_generated",
        sampling_stratum=pair["group"],
        candidate_id=pair.get("candidate_id"),
        selection_utc=selection_utc,
        inclusion_rationale="IN1: both sides >= 4 usable corpus records at screening",
        citation_gap_rationale="not_applicable_at_sampling: citation-gap criteria are an evaluation output, not a sampling criterion (protocol §12)",
    )


def _make_dataset(cases: list[EvaluationCase], corpus_used: list[str]) -> EvaluationDataset:
    ds = EvaluationDataset(
        dataset_id="real_case_study_v2",
        version="1.0.0",
        description=(
            "v2 benchmark dataset for the ResearchCollision evaluation, constructed by the frozen "
            "CASE_SAMPLING_PROTOCOL.md from a 30-domain pool grouped into 4 discipline strata, with "
            "seeded stratified sampling (seed 20260925), eligibility screening, and multi-corpus "
            "evidence retrieval (OpenAlex required; PubMed for life/health domains; arXiv best-effort). "
            "Every source record is real and publicly traceable; machine-generated labels are declared "
            "via annotation_provenance. Sampling artifacts live in datasets/v2; the v1 pilot (12 cases) "
            "is preserved unchanged in datasets/v1."
        ),
        provenance="curated",
        is_synthetic=False,
        label="REAL CASE-STUDY DATASET v2 — SOURCE PAPERS ARE PUBLICLY TRACEABLE",
        created_utc=_utcnow(),
        source_providers=sorted(corpus_used),
        annotation_provenance={
            "source_papers": "provider_metadata",
            "expected_topics": "machine_generated",
            "expected_methods": "none",
            "expected_gaps": "none",
            "expected_evidence_references": "machine_generated",
        },
        notes=(
            "Built by evaluation.datav2.build following CASE_SAMPLING_PROTOCOL.md. researcher_a/"
            "researcher_b are illustrative domain personas, not real named individuals. "
            "expected_topics and expected_evidence_references are machine-generated heuristics "
            "and are NOT expert gold; no gap annotation exists (reported n/a)."
        ),
        cases=cases,
    )
    ds.content_sha256 = ds.compute_content_sha256()
    return ds


def _v1_snapshot() -> dict[str, Any]:
    """Read-only snapshot of the v1 pilot under datasets/v1 (byte-identical copies)."""
    v1_root = ROOT.parent / "v1"
    v1_root.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {
        "kind": "v1_pilot_snapshot",
        "note": "Read-only byte-identical snapshot of the immutable v1 pilot. Source files are never modified.",
        "files": {},
    }
    for name, allow_fail in (("real_case_study_v1.json", False), ("real_case_specs_v1.json", False), ("demo_discovery.json", True)):
        src = DATA / name
        if not allow_fail and not src.exists():
            raise FileNotFoundError(f"authoritative v1 file missing: {src}")
        if allow_fail and not src.exists():
            continue
        dest = v1_root / name
        if dest.exists() and _sha256_file(dest) != _sha256_file(src):
            raise RuntimeError(f"datasets/v1/{name} exists with different content; refusing to overwrite")
        if not dest.exists():
            dest.write_bytes(src.read_bytes())
        manifest["files"][name] = {
            "source": str(src),
            "sha256": _sha256_file(dest),
            "size_bytes": dest.stat().st_size,
        }
    _write_json(v1_root / "MANIFEST.json", manifest)
    return manifest


_frame_map: dict[str, Any] = {}


def _write_dataset_card(root: Path, manifest: dict[str, Any], ds: EvaluationDataset, selected_ids: list[str]) -> Path:
    """Emit DATASET_CARD.md (protocol §3L output) summarizing the v2 build."""
    p = s.load_pool()
    univ = s.universe(p)
    global _frame_map
    _frame_map = {q["pair_id"]: q for q in univ}

    corpora = manifest["corpora"]
    dedup = manifest["dedup"]

    rows = []
    for g, n in sorted(manifest["strata"]["groups"].items()):
        rows.append(
            f"| `{g}` | {n} | {manifest['strata']['frame_allocation'].get(g, 0)}"
            f" | {manifest['strata']['eligible_by_group'].get(g, 0)}"
            f" | {sum(1 for i in selected_ids if _frame_map.get(i, {}).get('group') == g)} |"
        )

    drop_lines = "\n".join(
        f"- `{d['pair_id']}`: {d['error'][:120]}" for d in manifest["build"]["dropped_at_build"]
    ) or "- none"

    card = f"""# Dataset Card — v2 Crossing-Pair Discovery Benchmark

- **Protocol:** `CASE_SAMPLING_PROTOCOL.md` (frozen, sha256 `{manifest['protocol_sha256'][:16]}…`)
- **Sampling seed:** `{manifest['sampling_seed']}` · **method:** stratified seeded sampling
  (proportional allocation, largest-remainder; see protocol §6/§9)
- **Domain pool:** `evaluation/datav2/domain_pool_v1.json` (30 domains, sha256 `{manifest['pool_sha256'][:16]}…`)
- **Built:** `{manifest['created_utc']}` · **selection:** `{manifest['selection_utc']}`
- **Dataset file:** `dataset_v2.json` · sha256 `{ds.content_sha256}`
- **Status:** complete, immutable. Do not rebuild in place (see protocol §3I).

## Summary numbers

| Metric | Value |
|---|---|
| Pairing universe (all unordered domain pairs) | `{manifest['universe_size']}` |
| Candidate frame | `{manifest['frame_size']}` |
| Screened | `{manifest['screened']}` |
| Eligible (IN_T={s.IN_T}) | `{manifest['eligible']}` |
| Target sample | `{manifest['final_sample']['target']}` |
| Selected | `{manifest['final_sample']['selected']}` (reserve used: `{manifest['final_sample']['reserve_used']}`) |
| Final dataset size | `{manifest['build']['final_dataset_size']}` cases |
| Records before dedup / kept | `{dedup['total_records_before_dedup']}` / `{dedup['kept_after_dedup']}` |
| Dropped at build | {len(manifest['build']['dropped_at_build'])} |

## Exclusion reasons (screening)

```json
{json.dumps(manifest['excluded_by_reason'], indent=2, sort_keys=True)}
```

## Copora access

- OpenAlex: always (screening + build), polite-pool mailto `buildbyfarid@gmail.com`.
- PubMed: used when a side's domain is `biomed` (protocol §3E).
- arXiv: best-effort, never blocks. Probe this session: `{corpora.get('arxiv_probe_ok')}`.
- API calls: {json.dumps(corpora['calls'])}
- Corpus errors: {json.dumps(corpora['errors'])}
- OpenAlex screening errors: {json.dumps(corpora['openalex_errors'])}

## Stratum distribution

| Group | Universe | Frame alloc | Eligible | Selected |
|---|---|---|---|---|
{''.join(rows)}

## Dedup (protocol §10)

Hierarchy: DOI → normalized title+year → provider id → normalized-title fallback (flagged).

Matcher casualties: {json.dumps(dedup['dropped_by_matcher'])}
Audit log: `dedup_audit.json`.

## Provenance

- Case ids: `v2_<domain_a>_<domain_b>` with `candidate_id`/`sampling_stratum`/
  `selection_utc`/`inclusion_rationale`/`citation_gap_rationale` on each case (§3D).
- Each source paper records `source_provider`, `provider_id`, `doi`, `retrieved_utc`
  (corpus access date) and `evidence_text` (abstract) (§3E, §3D).
- v1 pilot is untouched (byte-identical snapshot + sha256 pin in `datasets/v1/MANIFEST.json`)
  and never mixed with v2 (§3I). Mapping: `datasets/v1/v1_to_v2_mapping.json`.

## Files

- `dataset_v2.json` — final dataset (sha256 `{ds.content_sha256}`)
- `candidate_frame.json` — deterministic 96-pair frame
- `candidate_population.json` — screening results
- `sampling_manifest.json` — full numbers, seeds, reasons, errors
- `dedup_audit.json` — dedup trace
- `DATASET_CARD.md` — this file

## Limitations

- {len(manifest['build']['dropped_at_build'])} selected case(s) dropped at build:
{drop_lines}
- arXiv may be under-represented if the API was unavailable during the build window.
- Screening/selection never used system outputs (protocol §3J); no evaluation ran on v2.
"""
    dest = root / "DATASET_CARD.md"
    dest.write_text(card, encoding="utf-8")
    return dest


def _v1_to_v2_mapping(selected: list[str]) -> dict[str, Any]:
    mapping: dict[str, Any] = {"seed": s.SEED, "note": "v1->v2 correspondence; v1 is unchanged.", "cases": {}}
    for v1_id, cand in V1_PAIR_CANDIDATES.items():
        if cand is None:
            mapping["cases"][v1_id] = {"status": "not_resampled", "reason": "no counterpart domain pair defined in the v2 pool"}
            continue
        cand_pair = f"v2_{cand[0]}_{cand[1]}"
        mapping["cases"][v1_id] = {
            "status": "resampled_v2" if cand_pair in selected else "not_resampled",
            "v2_pair_id": cand_pair,
            "note": "identical domain pairing occurred in the seeded random sample OR remained unsampled; v1 case itself is preserved untouched in every case",
        }
    return mapping


async def build(root: Path = ROOT, screen_only: bool = False) -> dict[str, Any]:
    if root.exists() and any(root.iterdir()):
        allowed = {"candidate_frame.json", "candidate_population.json", "corpus_query_cache.json"}
        present = {p.name for p in root.iterdir()}
        if not present.issubset(allowed):
            raise RuntimeError(
                f"{root} contains files outside the resume set {sorted(allowed)}; "
                "refusing to overwrite existing artifacts (immutability convention)"
            )
    root.mkdir(parents=True, exist_ok=True)

    from app.providers.literature.arxiv import ArxivProvider
    from app.providers.literature.openalex import OpenAlexProvider
    from app.providers.literature.pubmed import PubmedProvider

    pool = s.load_pool()
    pool_hash = s.pool_sha256()
    frame = s.build_frame(pool)
    _write_json(root / "candidate_frame.json", {"pool_id": "domain_pool_v1", "pool_sha256": pool_hash, "seed": s.SEED, "n": len(frame), "candidates": frame})

    screen_provider = _OpenAlexWithRetry(OpenAlexProvider())
    cache_path = root / "corpus_query_cache.json"
    pop_path = root / "candidate_population.json"
    if pop_path.exists():
        screened = json.loads(pop_path.read_text(encoding="utf-8"))["candidates"]
        print(f"[screen] reusing existing candidate_population.json ({len(screened)} records)", flush=True)
        cache = _load_cache(cache_path, pool_hash, s.SEED)
        if not cache.get("records"):
            raise RuntimeError("existing candidate_population.json without a valid OpenAlex query cache — inconsistent checkpoint")
    else:
        try:
            cache = await _fetch_screening_queries(frame, screen_provider, cache_path, pool_hash, s.SEED)
        except (CorpusCooldownError, ProviderError) as exc:
            print(
                f"[screen] ABORT: {exc}\n"
                "[screen] provider access failed (429 hard cooldown or persistent failure). "
                "Every already-fetched query is saved in corpus_query_cache.json; "
                "candidate_frame.json checkpoint preserved. Screening gate FAILED.",
                flush=True,
            )
            raise SystemExit(2) from exc
        screened = _screen_candidates(frame, cache)
        _write_json(pop_path, {"seed": s.SEED, "queries_fetched": len(cache["records"]), "candidates": screened})

    eligible = [r["pair_id"] for r in screened if r["decision"] == "eligible"]
    provider_failed = sum(1 for r in screened if r["decision"] == "excluded_provider")
    if provider_failed:
        print(
            f"[screen] WARNING {provider_failed}/{len(screened)} candidates failed for provider reasons "
            "(EX2); these usually indicate corpus throttling.",
            flush=True,
        )
    if not eligible:
        raise RuntimeError(
            "screening produced 0 eligible candidates — corpus access likely throttled/blocked; "
            "refusing to build an empty v2 dataset. Check feasibility_report.md and retry after cooldown."
        )
    if screen_only:
        ec = {r["decision"]: sum(1 for x in screened if x["decision"] == r["decision"]) for r in screened}
        print(
            f"[screen-only] screened={len(screened)} decisions={ec} "
            f"eligible={len(eligible)} of target {s.N_TARGET} | "
            f"openalex_queries_fetched={len(cache['records'])}",
            flush=True,
        )
        return {"screen_only": True, "screened": len(screened), "eligible": len(eligible)}

    result = s.select_final(eligible, pool)
    selected_ids = result["selected"]
    selection_utc = _utcnow()

    chosen = [p for p in frame if p["pair_id"] in set(selected_ids)]
    provider_map = {
        "pubmed": PubmedProvider(),
        "arxiv": ArxivProvider(),
    }
    stats: dict[str, Any] = {"dedup_audit": [], "dropped_at_build": []}
    arxiv_ok, arxiv_err = await _probe_arxiv(provider_map["arxiv"])
    stats["arxiv_ok"] = arxiv_ok
    stats.setdefault("calls", {})["openalex"] = list(cache["records"].keys())  # reused, not re-fetched
    if not arxiv_ok:
        stats.setdefault("corpus_errors", []).append(
            {"corpus": "arxiv", "query": "PROBE", "error": arxiv_err, "skipped": True}
        )
        print(f"[arxiv] probe failed -> arXiv skipped this session: {arxiv_err}", flush=True)
    else:
        print("[arxiv] probe OK -> arXiv enabled (best-effort)", flush=True)
    cases: list[EvaluationCase] = []
    for p in sorted(chosen, key=lambda x: x["pair_id"]):
        ok = False
        for attempt in (1, 2):
            try:
                cases.append(await _build_case(p, pool, provider_map, stats, selection_utc, cache))
                print(f"[build] {p['pair_id']}: ok", flush=True)
                ok = True
                break
            except Exception as exc:  # transient network errors retried once
                if attempt == 1:
                    print(f"[build] {p['pair_id']}: retry after {type(exc).__name__}", flush=True)
                    await asyncio.sleep(1.5)
                else:
                    stats["dropped_at_build"].append({"pair_id": p["pair_id"], "error": str(exc)[:300]})
                    print(f"[build] {p['pair_id']}: DROPPED ({type(exc).__name__}: {exc})", flush=True)

    corpus_used = sorted(
        {
            c
            for c in CORPUS_ORDER
            if (stats.get("calls", {}).get(c))
        }
    )
    ds = _make_dataset(cases, corpus_used or ["openalex"])
    _write_json(root / "dataset_v2.json", ds.model_dump(mode="json"))

    dedup_audit = stats["dedup_audit"]
    kept = [a["kept"] for a in dedup_audit]
    by_matcher: dict[str, int] = {}
    for a in dedup_audit:
        if a["matcher"]:
            by_matcher[a["matcher"]] = by_matcher.get(a["matcher"], 0) + 1
    _write_json(
        root / "dedup_audit.json",
        {
            "total_records_before_dedup": len(dedup_audit),
            "kept_after_dedup": sum(kept),
            "dropped_by_matcher": by_matcher,
            "entries": dedup_audit,
        },
    )

    screened_decision_counts: dict[str, int] = {}
    reasons: dict[str, int] = {}
    for r in screened:
        screened_decision_counts[r["decision"]] = screened_decision_counts.get(r["decision"], 0) + 1
        reasons[r["reason"]] = reasons.get(r["reason"], 0) + 1

    api_calls = {c: len(v) for c, v in stats.get("calls", {}).items()}
    manifest = {
        "kind": "v2_sampling_manifest",
        "protocol_file": str(PROTOCOL),
        "protocol_sha256": _sha256_file(PROTOCOL),
        "pool_file": "evaluation/datav2/domain_pool_v1.json",
        "pool_sha256": pool_hash,
        "sampling_seed": s.SEED,
        "method": "stratified seeded sampling (proportional, largest remainder) from all unordered domain pairs",
        "created_utc": _utcnow(),
        "selection_utc": selection_utc,
        "universe_size": len(s.universe(pool)),
        "frame_size": len(frame),
        "screened": len(screened),
        "eligible": len(eligible),
        "excluded_by_reason": reasons,
        "screening_decisions": screened_decision_counts,
        "candidate_counts": {
            "screened": len(screened),
            "eligible": len(eligible),
            "excluded": len(screened) - len(eligible),
        },
        "strata": {
            "groups": {g: n for g, n in sorted(s.group_sizes(pool).items())},
            "frame_allocation": result["alloc"],
            "eligible_by_group": result["eligible_by_group"],
            "shortfalls": result["shortfalls"],
        },
        "final_sample": {
            "target": s.N_TARGET,
            "selected": len(selected_ids),
            "selected_ids": selected_ids,
            "reserve_used": result["reserve_used"],
        },
        "dedup": {
            "total_records_before_dedup": len(dedup_audit),
            "kept_after_dedup": sum(kept),
            "dropped_by_matcher": by_matcher,
        },
        "request_optimization": {
            "strategy": "per-domain OpenAlex query cache (corpus_query_cache.json): each of the distinct frame queries is fetched exactly once; screening decisions and build-time records are computed/reused from the cache, so OpenAlex is never re-queried per candidate",
            "naive_openalex_search_calls": {
                "screening": (2 * len(frame)),
                "build": (2 * len(chosen)),
                "total": (2 * len(frame)) + (2 * len(chosen)),
            },
            "optimized_openalex_search_calls": {
                "screening": len(cache["records"]),
                "build": 0,
                "total": len(cache["records"]),
            },
            "distinct_queries_cached": len(cache["records"]),
            "reduction_percent": round(
                100.0 * (1.0 - len(cache["records"]) / max(1, (2 * len(frame)) + (2 * len(chosen)))),
                1,
            ),
        },
        "build": {
            "dropped_at_build": stats["dropped_at_build"],
            "final_dataset_size": len(cases),
            "records_in_dataset": len(ds.cases) and sum(len(c.source_papers) for c in ds.cases),
            "per_side_selection": {
                "slots": "openalex<=3, pubmed<=1, arxiv<=1 per side, remainder pooled by citations",
                "per_side": PER_SIDE,
            },
        },
        "corpora": {
            "calls": api_calls,
            "arxiv_probe_ok": stats.get("arxiv_ok"),
            "errors": stats.get("corpus_errors", []),
            "openalex_errors": screen_provider.errors,
            "used": corpus_used,
        },
        "artifacts": {
            "dataset_v2.json": ds.content_sha256,
            "candidate_frame.json": _sha256_file(root / "candidate_frame.json"),
            "candidate_population.json": _sha256_file(root / "candidate_population.json"),
            "corpus_query_cache.json": _sha256_file(root / "corpus_query_cache.json"),
        },
    }
    _write_json(root / "sampling_manifest.json", manifest)

    _write_dataset_card(root, manifest, ds, selected_ids)

    v1_manifest = _v1_snapshot()
    _write_json(root.parent / "v1" / "v1_to_v2_mapping.json", _v1_to_v2_mapping(selected_ids))

    return {
        "manifest": manifest,
        "v1_manifest": v1_manifest,
        "dataset_sha256": ds.content_sha256,
        "n_cases": len(cases),
    }


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="evaluation.datav2.build", description="Build the v2 dataset per CASE_SAMPLING_PROTOCOL.md.")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--screen-only", action="store_true", help="Run eligibility screening only.")
    args = parser.parse_args(argv)
    result = asyncio.run(build(Path(args.root), screen_only=args.screen_only))
    if result.get("screen_only"):
        return 0
    print(
        f"v2 dataset complete: {result['n_cases']} cases "
        f"(sha256={result['dataset_sha256'][:12]}...), artifacts under {Path(args.root)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())