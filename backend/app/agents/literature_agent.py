"""Literature Agent — builds queries and fetches papers via provider chain."""
from __future__ import annotations

import structlog

from app.providers.literature.factory import LiteratureProviderChain

logger = structlog.get_logger(__name__)

STOP_QUERY_TERMS = {"and", "or", "the", "of", "for", "with", "a", "an", "in", "on"}


class LiteratureAgent:
    """Not LLM-driven: deterministic query construction + provider fallback."""

    name = "literature_agent"

    def __init__(self, chain: LiteratureProviderChain | None = None) -> None:
        self.chain = chain or LiteratureProviderChain()

    def build_queries(
        self,
        *,
        interests_a: list[str],
        interests_b: list[str] | None = None,
        field_query: str | None = None,
        max_queries: int = 4,
    ) -> list[str]:
        queries: list[str] = []
        if field_query:
            queries.append(field_query)
        shared = [t for t in interests_a if interests_b and t in interests_b]
        for t in (shared + interests_a)[:max_queries]:
            q = t.strip()
            if q and q.lower() not in STOP_QUERY_TERMS and q not in queries:
                queries.append(q)
        return queries[:max_queries]

    async def search(self, query: str, limit: int = 10) -> tuple[list, str]:
        papers, provider = await self.chain.search(query, limit=limit)
        logger.info("literature.search", query=query, provider=provider, count=len(papers))
        return papers, provider
