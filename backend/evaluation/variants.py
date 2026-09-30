"""Phase 4C controlled pipeline variants (benchmark-only; never production).

Three experimental conditions, each activated by ``EVAL_PIPELINE_VARIANT``
(``live`` is the default and is byte-for-byte the original pipeline):

* ``live_cache``    (condition A)  - persistent literature-retrieval cache.
  Disk-backed, append-only (never overwrites an existing key), keyed by
  ``(stripped/lowercased query, limit)`` - every parameter that currently
  affects retrieval. The FIRST fetch of a key is a live call, exactly as the
  original pipeline performs it; every later identical request replays that
  stored snapshot byte-for-byte. Records + ordering are preserved.
* ``analysis_cache`` (condition B) - within-run paper-analysis cache. An
  in-memory cache scoped to a single pipeline invocation (a single seed), so
  each seed retains its own stochastic/LLM execution path (cross-seed reuse
  is explicitly prohibited). Keyed by the canonical paper identity, the exact
  model, model parameters, and the exact analysis prompt/version/config.
* ``frozen_v2``     (condition F) - retrieval replaced by the frozen v2 corpus
  (each case's ``source_papers``), no live retrieval, analysed as a separate
  experimental condition, never as the production pipeline.

None of these variants alter prompts, models, retrieval depth, evidence
criteria, case definitions, system logic, provider/rate-limit behavior, or
concurrency. Every variant is additive; ``live`` is the unmodified pipeline.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any

import structlog

from app.providers.literature.base import PaperMetadata
from app.services.literature_service import LiteratureService
from app.workers.tasks.discovery_pipeline import DiscoveryPipeline

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Registry used by the benchmark harness to collect audit evidence
# ---------------------------------------------------------------------------

_LIT_REGISTRY: list[Any] = []
_STATS_REGISTRY: list[dict[str, Any]] = []


def register_lit_service(svc: Any) -> None:
    _LIT_REGISTRY.append(svc)


def drain_lit_services() -> list[Any]:
    out, _LIT_REGISTRY[:] = list(_LIT_REGISTRY), []
    return out


def register_stats(stats: dict[str, Any]) -> None:
    _STATS_REGISTRY.append(stats)


def drain_stats() -> list[dict[str, Any]]:
    out, _STATS_REGISTRY[:] = list(_STATS_REGISTRY), []
    return out


# ---------------------------------------------------------------------------
# Content-hash helper (byte-equivalence for retrieval snapshots)
# ---------------------------------------------------------------------------


def _papers_payload(papers: list[PaperMetadata], provider: str) -> str:
    return json.dumps(
        {"provider": provider, "papers": [asdict(p) for p in papers]},
        sort_keys=True,
        default=str,
    )


def content_sha256(papers: list[PaperMetadata], provider: str) -> str:
    return hashlib.sha256(_papers_payload(papers, provider).encode("utf-8")).hexdigest()


def _deserialize_papers(raw: list[dict[str, Any]]) -> list[PaperMetadata]:
    return [PaperMetadata(**p) for p in raw]


# ---------------------------------------------------------------------------
# Condition A: persistent, append-only literature retrieval cache
# ---------------------------------------------------------------------------


class PersistentLiteratureService(LiteratureService):
    """Like ``LiteratureService`` but with a durable append-only disk cache.

    The disk cache is keyed by the exact key the in-memory service already
    used (``query.strip().lower() + '::' + limit``), which is every parameter
    that affects retrieval today. Keys are written once and never overwritten,
    so the first live fetch of each query is the permanent snapshot; later
    identical requests replay it byte-for-byte.
    """

    def __init__(
        self,
        chain: Any | None = None,
        *,
        cache_path: str | Path | None = None,
        audit_path: str | Path | None = None,
    ) -> None:
        super().__init__(chain=chain)
        self.cache_path = Path(cache_path or os.getenv("EVAL_LIT_CACHE_PATH") or _default_cache_path())
        self.audit_path = Path(audit_path or os.getenv("EVAL_LIT_AUDIT_PATH") or (self.cache_path.with_suffix(".audit.jsonl")))
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        self._entries: dict[str, dict[str, Any]] = self._load()
        self.audit_entries: list[dict[str, Any]] = []
        self._replay_mismatches: list[dict[str, Any]] = []

    @staticmethod
    def _default_cache_path() -> Path:
        return Path(tempfile.gettempdir()) / "opencode" / "p4c_cache" / "lit_cache.json"

    def _load(self) -> dict[str, dict[str, Any]]:
        if not self.cache_path.exists():
            return {}
        try:
            data = json.loads(self.cache_path.read_text(encoding="utf-8"))
            return data.get("entries", {})
        except (json.JSONDecodeError, OSError):
            return {}

    def _save(self) -> None:
        tmp = self.cache_path.with_suffix(".tmp")
        payload = {
            "schema_version": 1,
            "note": (
                "Retrieval snapshot cache (condition A). Keys are written once and "
                "never overwritten; each key preserves the first live fetch exactly."
            ),
            "entries": self._entries,
        }
        tmp.write_text(json.dumps(payload, sort_keys=True, indent=2, default=str), encoding="utf-8")
        os.replace(tmp, self.cache_path)

    def _write_audit_line(self, entry: dict[str, Any]) -> None:
        self.audit_entries.append(entry)
        try:
            with self.audit_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, sort_keys=True, default=str) + "\n")
        except OSError:  # pragma: no cover - audit must never break retrieval
            pass

    async def search(
        self,
        query: str,
        *,
        limit: int = 10,
        refresh: bool = False,
    ) -> tuple[list[PaperMetadata], str]:
        key = f"{query.strip().lower()}::{limit}"
        if not refresh:
            cached = self._entries.get(key)
            if cached is not None:
                papers = _deserialize_papers(cached["papers"])
                replay_sha = content_sha256(papers, cached["provider"])
                match = replay_sha == cached.get("content_sha256")
                if not match:
                    self._replay_mismatches.append(
                        {"key": key, "replay_sha": replay_sha, "stored_sha": cached.get("content_sha256")}
                    )
                self._write_audit_line(
                    {
                        "event": "replay",
                        "key": key,
                        "query": query,
                        "limit": limit,
                        "provider": cached["provider"],
                        "count": len(papers),
                        "content_sha256": replay_sha,
                        "byte_equal_to_stored": match,
                    }
                )
                return papers, cached["provider"]
        try:
            papers, provider = await self.chain.search(query, limit=limit)
        except Exception as exc:
            # Failures are recorded but never cached (no negative caching: a
            # transient provider error must not mask later successes) and are
            # re-raised exactly as the base service would.
            self._write_audit_line(
                {
                    "event": "live_fetch_failed",
                    "key": key,
                    "query": query,
                    "limit": limit,
                    "error": str(exc)[:300],
                }
            )
            raise
        if papers:
            sha = content_sha256(papers, provider)
            self._entries.setdefault(
                key,
                {"papers": [asdict(p) for p in papers], "provider": provider, "content_sha256": sha},
            )
            self._save()
        self._write_audit_line(
            {
                "event": "live_fetch",
                "key": key,
                "query": query,
                "limit": limit,
                "provider": provider,
                "count": len(papers),
                "content_sha256": content_sha256(papers, provider) if papers else None,
            }
        )
        return papers, provider


# ---------------------------------------------------------------------------
# Condition F: retrieval from the frozen v2 corpus (separate condition)
# ---------------------------------------------------------------------------


class FrozenV2LiteratureService:
    """Returns the frozen v2 corpus papers for the case - no live retrieval.

    This is a separate experimental condition (``pipeline-frozen-v2-retrieval``),
    never a substitute for the live pipeline. The corpus papers were themselves
    real records at v2 build time (not synthetic).
    """

    name = "frozen_v2"

    def __init__(self, source_papers: list[Any]) -> None:
        self.papers = [self._to_meta(p) for p in source_papers]
        self.chain = None  # literature agent only uses .chain for query building

    @staticmethod
    def _to_meta(sp: Any) -> PaperMetadata:
        return PaperMetadata(
            title=sp.title,
            abstract=sp.abstract or None,
            authors=list(sp.authors),
            year=sp.year,
            doi=sp.doi,
            venue=sp.venue,
            source_provider=sp.source_provider or "openalex",
            provider_id=sp.provider_id or sp.paper_id,
            source_url=sp.source_url,
            citation_count=sp.citation_count or 0,
            topics=list(sp.topics),
            is_synthetic=False,
        )

    async def search(self, query: str, *, limit: int = 10, refresh: bool = False) -> tuple[list[PaperMetadata], str]:
        return self.papers, "frozen_v2"


# ---------------------------------------------------------------------------
# Condition B: within-run paper-analysis cache
# ---------------------------------------------------------------------------


# Per-seed, in-memory, process-scoped paper-analysis cache (condition B).
# A seed shares one cache across the cases of its run; the cache dies with the
# process, so seeds never reuse each other's LLM analyses (E: no cross-seed
# reuse). Each key already encodes the paper identity, model, parameters,
# prompt/version, and seed.
_PA_CACHE_BY_SEED: dict[int | None, dict[str, dict[str, Any]]] = {}


def _analysis_cache_key(agent: Any, llm: Any, seed: int | None, paper_identity: dict[str, Any]) -> str:
    from app.agents.base import compute_input_hash

    try:
        prompt_text = agent.load_prompt()
    except Exception:
        prompt_text = ""
    max_tokens = None
    try:
        from app.core.config import settings

        max_tokens = settings.structured_max_tokens
    except Exception:
        max_tokens = None
    payload = {
        "paper": compute_input_hash(paper_identity),
        "provider": getattr(llm, "name", "unknown"),
        "model": getattr(llm, "model", "unknown"),
        "seed": seed,
        "prompt_sha256": hashlib.sha256((prompt_text or "").encode("utf-8")).hexdigest(),
        "prompt_version": agent.prompt_version,
        "task_name": agent.task_name,
        "output_schema": agent.output_schema_name,
        "temperature": 0.2,
        "max_tokens": max_tokens,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


class PaperAnalysisCachePipeline(DiscoveryPipeline):
    """DiscoveryPipeline with a per-seed paper-analysis cache (condition B).

    One cache per seed, shared across the cases of that seed's run (in-memory,
    dies with the process, never persisted) - mirroring the within-seed
    comparison the benchmark requires. Cross-seed reuse is impossible by
    construction. Each key encodes the canonical paper identity, the exact
    model, model parameters, and the exact analysis prompt/version/config. On
    a hit the stored LLM content is replayed (no second LLM draw for an
    identical paper) and the per-case evidence id is re-attached, matching the
    linkage the uncached step performs.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._pa_cache = _PA_CACHE_BY_SEED.setdefault(self.seed, {})
        self._pa_stats: dict[str, Any] = {}

    async def step_analyze_papers(self) -> None:
        from app.agents.paper_analysis_agent import PaperAnalysisAgent

        agent = PaperAnalysisAgent(
            self.llm, db=self.db, workspace_id=self.workspace_id, job_id=self.job.id, seed=self.seed
        )
        self._paper_analyses = []
        stats = {"requests": 0, "unique": 0, "hits": 0, "misses": 0}
        errors = 0
        for paper in self._papers:
            try:
                ev = self.evidence_service.for_paper(
                    self.workspace_id,
                    paper,
                    claim=f"Paper '{paper.title}' reports findings relevant to the searched literature.",
                )
                paper_identity = {
                    "title": paper.title,
                    "abstract": paper.abstract or "",
                    "year": paper.publication_year,
                    "venue": paper.venue,
                    "domain_hint": (
                        paper.topics[0].name if hasattr(paper, "topics") and paper.topics else None
                    ),
                }
                key = _analysis_cache_key(agent, self.llm, self.seed, paper_identity)
                stats["requests"] += 1
                cached = self._pa_cache.get(key)
                if cached is not None:
                    stats["hits"] += 1
                    ad = dict(cached)
                else:
                    stats["misses"] += 1
                    stats["unique"] += 1
                    analysis = await agent.analyze(
                        title=paper.title,
                        abstract=paper.abstract or "",
                        year=paper.publication_year,
                        venue=paper.venue,
                        domain_hint=paper_identity["domain_hint"],
                        evidence_id=ev.id,
                    )
                    ad = analysis.model_dump()
                    self._pa_cache[key] = dict(ad)
                ad["title"] = paper.title
                ad["evidence_id"] = ev.id
                self._paper_analyses.append(ad)
                self.paper_service.link_methods(paper.id, ad.get("methods", []))
                self.paper_service.link_datasets(paper.id, ([ad["dataset"]] if ad.get("dataset") else []))
                await self.vector_service.embed_and_store(
                    entity_type="paper",
                    entity_id=paper.id,
                    text=f"{paper.title}\n{(paper.abstract or '')[:800]}",
                    workspace_id=self.workspace_id,
                )
            except Exception as exc:
                errors += 1
                logger.warning("pipeline.paper_analysis_failed", paper=paper.title[:60], error=str(exc)[:150])
                self.job_repo.add_event(
                    self.job.id, "item_failed", f"Analysis failed for '{paper.title[:60]}'"
                )
                continue
        self._pa_stats = {**stats, "cache_keys": len(self._pa_cache)}
        register_stats({"kind": "analysis_cache", "case_id": getattr(self, "_variant_case_id", "?"), **stats})
        self.db.commit()
        self.result_summary["papers_analyzed"] = len(self._paper_analyses)
        self.result_summary["analysis_errors"] = errors


# ---------------------------------------------------------------------------
# Variant builder (single switch point used by the evaluation baseline)
# ---------------------------------------------------------------------------


def build_pipeline_variant(db: Any, job: Any, *, seed: int | None, case: Any) -> Any:
    """Return the pipeline/retrieval for the active variant (default: ``live``)."""
    variant = os.getenv("EVAL_PIPELINE_VARIANT", "live")
    if variant == "analysis_cache":
        pipe = PaperAnalysisCachePipeline(db, job, seed=seed)
    elif variant == "frozen_v2":
        svc = FrozenV2LiteratureService(case.source_papers)
        pipe = DiscoveryPipeline(db, job, seed=seed, literature=svc)
    elif variant == "live_cache":
        svc = PersistentLiteratureService()
        register_lit_service(svc)
        pipe = DiscoveryPipeline(db, job, seed=seed, literature=svc)
    else:
        pipe = DiscoveryPipeline(db, job, seed=seed)
    pipe._variant_case_id = case.case_id
    return pipe