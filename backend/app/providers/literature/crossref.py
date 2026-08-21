"""Crossref literature provider."""
from __future__ import annotations

import httpx
import structlog

from app.core.config import settings
from app.core.exceptions import ProviderError
from app.providers.literature.base import PaperMetadata, clean_doi

logger = structlog.get_logger(__name__)
BASE_URL = "https://api.crossref.org"


class CrossrefProvider:
    name = "crossref"

    def _headers(self) -> dict:
        ua = "ResearchCollision/1.0 (mailto:%s)" % settings.crossref_email if settings.crossref_email else "ResearchCollision/1.0"
        return {"User-Agent": ua}

    async def search(self, query: str, *, limit: int = 10) -> list[PaperMetadata]:
        try:
            async with httpx.AsyncClient(timeout=settings.literature_timeout_seconds) as client:
                resp = await client.get(
                    f"{BASE_URL}/works",
                    params={"query": query, "rows": min(limit, 50)},
                    headers=self._headers(),
                )
                resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise ProviderError(f"Crossref search failed: {exc}") from exc
        items = resp.json().get("message", {}).get("items", [])
        papers = []
        for r in items[:limit]:
            year = None
            for date_field in ("published-print", "published-online", "issued"):
                parts = (r.get(date_field) or {}).get("date-parts") or []
                if parts and parts[0]:
                    year = parts[0][0]
                    break
            papers.append(
                PaperMetadata(
                    title=(r.get("title") or ["Untitled"])[0],
                    abstract=r.get("abstract"),
                    authors=[
                        f"{a.get('given', '')} {a.get('family', '')}".strip()
                        for a in r.get("author", [])
                    ],
                    year=year,
                    doi=clean_doi(r.get("DOI")),
                    venue=((r.get("container-title") or [None]) or [None])[0],
                    source_provider=self.name,
                    provider_id=r.get("DOI") or r.get("id", ""),
                    source_url=r.get("URL"),
                    citation_count=r.get("is-referenced-by-count", 0) or 0,
                )
            )
        return papers

    async def get_paper(self, provider_id: str) -> PaperMetadata | None:
        try:
            async with httpx.AsyncClient(timeout=settings.literature_timeout_seconds) as client:
                resp = await client.get(f"{BASE_URL}/works/{provider_id}", headers=self._headers())
                if resp.status_code == 404:
                    return None
                resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise ProviderError(f"Crossref get_paper failed: {exc}") from exc
        r = resp.json().get("message", {})
        return PaperMetadata(
            title=(r.get("title") or ["Untitled"])[0],
            abstract=r.get("abstract"),
            doi=clean_doi(r.get("DOI")),
            source_provider=self.name,
            provider_id=provider_id,
            source_url=r.get("URL"),
        )
