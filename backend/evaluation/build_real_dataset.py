"""Reproducible builder for the real case-study evaluation dataset.

Collects ONLY real, publicly traceable papers from a scholarly provider
(OpenAlex by default). No paper, DOI, author, gap, or annotation is invented:
if provider results are insufficient the build **fails loudly** rather than
fabricating records.

Annotation provenance is recorded explicitly in
``annotation_provenance`` so machine-generated labels are never confused with
independent human annotations:

* ``source_papers``               -> ``provider_metadata`` (real API records)
* ``expected_topics``             -> ``machine_generated`` (provider topic labels)
* ``expected_methods``            -> ``none`` (no normalized method annotation)
* ``expected_gaps``               -> ``none`` (no independent expert annotation)
* ``expected_evidence_references`` -> ``machine_generated`` (heuristic, see below)

The expected-evidence set is a documented heuristic (the N most-cited papers
of each case corpus); it is a *reference set*, not expert gold, and is labeled
as machine-generated everywhere it is shown.

Reproduce with::

    cd backend
    python -m evaluation.build_real_dataset \\
        --specs evaluation/data/real_case_specs_v1.json \\
        --out   evaluation/data/real_case_study_v1.json \\
        --mailto you@example.org        # optional (OpenAlex polite pool)

Requires network access to https://api.openalex.org.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from evaluation.schemas import (
    EvaluationCase,
    EvaluationDataset,
    ResearcherInput,
    SourcePaper,
)

REAL_LABEL = "REAL CASE-STUDY DATASET — SOURCE PAPERS ARE PUBLICLY TRACEABLE"
MAX_EVIDENCE_CHARS = 1500
DEFAULT_MIN_PAPERS = 4
DEFAULT_PER_DOMAIN = 5
DEFAULT_SEARCH_LIMIT = 25


class SearchProvider(Protocol):
    name: str

    async def search(self, query: str, *, limit: int = 10): ...


def _norm_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (title or "").lower())


def _paper_from_meta(meta, provider: str) -> SourcePaper | None:
    """Convert a provider record into a traceable SourcePaper, or None if unusable."""
    provider_id = getattr(meta, "provider_id", None)
    doi = getattr(meta, "doi", None)
    if not (provider_id or doi):
        return None
    abstract = (getattr(meta, "abstract", None) or "").strip()
    if not abstract:
        return None
    paper_id = str(provider_id) if provider_id else f"doi:{doi}"
    source_url = (
        f"https://doi.org/{doi}" if doi else f"https://openalex.org/{provider_id}"
    )
    return SourcePaper(
        paper_id=paper_id,
        title=(getattr(meta, "title", None) or "").strip() or "Untitled",
        abstract=abstract[:MAX_EVIDENCE_CHARS],
        evidence_text=abstract[:MAX_EVIDENCE_CHARS],
        year=getattr(meta, "year", None),
        venue=getattr(meta, "venue", None),
        doi=doi,
        topics=list(getattr(meta, "topics", None) or []),
        methods=[],
        authors=list(getattr(meta, "authors", None) or []),
        provider_id=provider_id,
        source_provider=provider,
        source_url=source_url,
        citation_count=getattr(meta, "citation_count", None),
    )


def _collect_domain(papers: list[SourcePaper], seen_titles: set[str], seen_dois: set[str]) -> list[SourcePaper]:
    out: list[SourcePaper] = []
    for p in papers:
        key = _norm_title(p.title)
        if key in seen_titles:
            continue
        if p.doi and p.doi in seen_dois:
            continue
        seen_titles.add(key)
        if p.doi:
            seen_dois.add(p.doi)
        out.append(p)
    return out


def _top_topics(papers: list[SourcePaper], limit: int = 12) -> list[str]:
    counts: Counter[str] = Counter()
    for p in papers:
        for t in p.topics:
            if t:
                counts[t] += 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return [t for t, _ in ranked[:limit]]


def _expected_evidence(papers: list[SourcePaper], k: int = 3) -> list[str]:
    """Heuristic (machine-generated) reference set: k most-cited corpus papers."""
    ranked = sorted(
        papers,
        key=lambda p: (-(p.citation_count or 0), p.paper_id),
    )
    return [p.paper_id for p in ranked[: min(k, len(ranked))]]


async def build_case(
    spec: dict[str, Any],
    provider: SearchProvider,
    *,
    min_papers: int = DEFAULT_MIN_PAPERS,
    per_domain: int = DEFAULT_PER_DOMAIN,
    search_limit: int = DEFAULT_SEARCH_LIMIT,
) -> EvaluationCase:
    case_id = spec["case_id"]

    async def fetch(query: str) -> list[SourcePaper]:
        metas = await provider.search(query, limit=search_limit)
        converted = [_paper_from_meta(m, provider.name) for m in metas]
        usable = [p for p in converted if p is not None]
        usable.sort(key=lambda p: (-(p.citation_count or 0), p.paper_id))
        return usable

    a_papers = await fetch(spec["query_a"])
    b_papers = await fetch(spec["query_b"])

    seen_titles: set[str] = set()
    seen_dois: set[str] = set()
    papers = _collect_domain(a_papers, seen_titles, seen_dois)[:per_domain]
    papers += _collect_domain(b_papers, seen_titles, seen_dois)[:per_domain]

    if len(papers) < min_papers:
        raise RuntimeError(
            f"Case {case_id!r}: only {len(papers)} usable real papers "
            f"(need >= {min_papers}). Queries: {spec['query_a']!r} / "
            f"{spec['query_b']!r}. Refusing to fabricate records."
        )

    a_topics = _top_topics(_collect_domain(a_papers, set(), set()), 6)
    b_topics = _top_topics(_collect_domain(b_papers, set(), set()), 6)

    researcher_a = ResearcherInput(
        name=spec["domain_a"],
        bio=f"Illustrative research-domain persona for '{spec['domain_a']}' "
            f"(built from real OpenAlex topic metadata; not a real individual).",
        topics=a_topics,
        methods=[],
        domains=[spec["domain_a"]],
    )
    researcher_b = ResearcherInput(
        name=spec["domain_b"],
        bio=f"Illustrative research-domain persona for '{spec['domain_b']}' "
            f"(built from real OpenAlex topic metadata; not a real individual).",
        topics=b_topics,
        methods=[],
        domains=[spec["domain_b"]],
    )

    return EvaluationCase(
        case_id=case_id,
        label=f"Real case: {spec['domain_a']} × {spec['domain_b']}",
        evaluation_question=spec.get("evaluation_question"),
        researcher_a=researcher_a,
        researcher_b=researcher_b,
        field_query=spec.get("field_query"),
        source_papers=papers,
        expected_topics=_top_topics(papers, 12),
        expected_methods=[],  # no independent method annotation available
        expected_gaps=[],  # no independent expert gap annotation available
        expected_evidence_references=_expected_evidence(papers, k=3),
        expected_evidence_source="machine_generated",
    )


async def build_dataset(
    specs: dict[str, Any],
    provider: SearchProvider,
    *,
    min_papers: int = DEFAULT_MIN_PAPERS,
    per_domain: int = DEFAULT_PER_DOMAIN,
    search_limit: int = DEFAULT_SEARCH_LIMIT,
    limit: int | None = None,
) -> EvaluationDataset:
    pairs = specs["domain_pairs"]
    if limit:
        pairs = pairs[:limit]
    cases = [
        await build_case(
            spec,
            provider,
            min_papers=min_papers,
            per_domain=per_domain,
            search_limit=search_limit,
        )
        for spec in pairs
    ]
    ds = EvaluationDataset(
        dataset_id=specs["dataset_id"],
        version=specs.get("version", "1.0.0"),
        description=specs.get("description", ""),
        provenance="curated",
        is_synthetic=False,
        label=REAL_LABEL,
        created_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        source_providers=[provider.name],
        annotation_provenance={
            "source_papers": "provider_metadata",
            "expected_topics": "machine_generated",
            "expected_methods": "none",
            "expected_gaps": "none",
            "expected_evidence_references": "machine_generated",
        },
        notes=(
            "Built by evaluation.build_real_dataset from "
            f"{provider.name} API results. researcher_a/researcher_b are "
            "illustrative domain personas, not real named individuals. "
            "expected_topics and expected_evidence_references are "
            "machine-generated heuristics (provider topic labels; N most-cited "
            "papers) and are NOT expert gold. No gap annotation exists for "
            "these cases; gap-relevance is therefore reported n/a."
        ),
        cases=cases,
    )
    ds.content_sha256 = ds.compute_content_sha256()
    return ds


def load_specs(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _default_provider():
    from app.providers.literature.openalex import OpenAlexProvider

    return OpenAlexProvider()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="evaluation.build_real_dataset",
        description="Build the real case-study dataset from a live scholarly provider.",
    )
    root = Path(__file__).resolve().parent
    parser.add_argument("--specs", default=str(root / "data" / "real_case_specs_v1.json"))
    parser.add_argument("--out", default=str(root / "data" / "real_case_study_v1.json"))
    parser.add_argument("--mailto", default=None, help="Contact email for the OpenAlex polite pool.")
    parser.add_argument("--min-papers", type=int, default=DEFAULT_MIN_PAPERS)
    parser.add_argument("--per-domain", type=int, default=DEFAULT_PER_DOMAIN)
    parser.add_argument("--search-limit", type=int, default=DEFAULT_SEARCH_LIMIT)
    parser.add_argument("--limit", type=int, default=None, help="Limit number of cases.")
    args = parser.parse_args(argv)

    if args.mailto:
        os.environ["OPENALEX_EMAIL"] = args.mailto

    specs = load_specs(args.specs)
    provider = _default_provider()
    ds = asyncio.run(
        build_dataset(
            specs,
            provider,
            min_papers=args.min_papers,
            per_domain=args.per_domain,
            search_limit=args.search_limit,
            limit=args.limit,
        )
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(ds.model_dump(mode="json"), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(
        f"Wrote {len(ds.cases)} real cases to {out} "
        f"(provider={provider.name}, sha256={ds.content_sha256[:12]}...)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
