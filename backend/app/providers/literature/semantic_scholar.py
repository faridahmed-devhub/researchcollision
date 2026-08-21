"""Semantic Scholar literature provider."""
from __future__ import annotations

import httpx
import structlog

from app.core.config import settings
from app.core.exceptions import ProviderError
from app.providers.literature.base import PaperMetadata, clean_doi

logger = structlog.get_logger(__name__)
BASE_URL = "https://api.semanticscholar.org/graph/v1"
FIELDS = "title,abstract,year,externalIds,venue,authors,citationCount,url"


class SemanticScholarProvider:
    name = "semantic_scholar"

    def _headers(self) -> dict:
        if settings.semantic_scholar_api_key:
            return {"x-api-key": settings.semantic_scholar_api_key}
        return {}

    async def search(self, query: str, *, limit: int = 10) -> list[PaperMetadata]:
        try:
            async with httpx.AsyncClient(timeout=settings.literature_timeout_seconds) as client:
                resp = await client.get(
                    f"{BASE_URL}/paper/search",
                    params={"query": query, "limit": min(limit, 100), "fields": FIELDS},
                    headers=self._headers(),
                )
                resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise ProviderError(f"Semantic Scholar search failed: {exc}") from exc
        papers = []
        for r in resp.json().get("data", [])[:limit]:
            ext = r.get("externalIds") or {}
            papers.append(
                PaperMetadata(
                    title=r.get("title") or "Untitled",
                    abstract=r.get("abstract"),
                    authors=[a.get("name", "") for a in r.get("authors", [])],
                    year=r.get("year"),
                    doi=clean_doi(ext.get("DOI")),
                    venue=r.get("venue") or None,
                    source_provider=self.name,
                    provider_id=r.get("paperId", ""),
                    source_url=r.get("url"),
                    citation_count=r.get("citationCount", 0) or 0,
                    external_ids=ext,
                )
            )
        return papers

    async def get_paper(self, provider_id: str) -> PaperMetadata | None:
        try:
            async with httpx.AsyncClient(timeout=settings.literature_timeout_seconds) as client:
                resp = await client.get(
                    f"{BASE_URL}/paper/{provider_id}",
                    params={"fields": FIELDS},
                    headers=self._headers(),
                )
                if resp.status_code == 404:
                    return None
                resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise ProviderError(f"Semantic Scholar get_paper failed: {exc}") from exc
        r = resp.json()
        ext = r.get("externalIds") or {}
        return PaperMetadata(
            title=r.get("title") or "Untitled",
            abstract=r.get("abstract"),
            authors=[a.get("name", "") for a in r.get("authors", [])],
            year=r.get("year"),
            doi=clean_doi(ext.get("DOI")),
            venue=r.get("venue") or None,
            source_provider=self.name,
            provider_id=provider_id,
            source_url=r.get("url"),
            external_ids=ext,
        )
