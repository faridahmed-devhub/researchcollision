"""OpenAlex literature provider (public API, polite pool via mailto)."""
from __future__ import annotations

from email.utils import parsedate_to_datetime
from datetime import datetime, timezone

import httpx
import structlog

from app.core.config import settings
from app.core.exceptions import ProviderError, ProviderThrottledError
from app.providers.literature.base import PaperMetadata, clean_doi

logger = structlog.get_logger(__name__)
BASE_URL = "https://api.openalex.org"


def _parse_retry_after(value: str | None) -> int | None:
    """Retry-After: either delta-seconds or an HTTP-date."""
    if not value:
        return None
    try:
        return max(0, int(value.strip()))
    except (TypeError, ValueError):
        pass
    try:
        when = parsedate_to_datetime(value.strip())
        secs = (when - datetime.now(timezone.utc)).total_seconds()
        return max(0, int(secs))
    except Exception:
        return None


class OpenAlexProvider:
    name = "openalex"

    def _params(self, extra: dict | None = None) -> dict:
        params = {"per-page": 25}
        if settings.openalex_email:
            params["mailto"] = settings.openalex_email
        if extra:
            params.update(extra)
        return params

    async def search(self, query: str, *, limit: int = 10) -> list[PaperMetadata]:
        try:
            async with httpx.AsyncClient(timeout=settings.literature_timeout_seconds) as client:
                resp = await client.get(
                    f"{BASE_URL}/works",
                    params=self._params({"search": query, "per-page": min(limit, 50)}),
                )
                if resp.status_code == 429:
                    # Respect the server's cooldown; this is NOT an empty result.
                    raise ProviderThrottledError(
                        "OpenAlex 429 Too Many Requests (rate limited)",
                        retry_after=_parse_retry_after(resp.headers.get("retry-after")),
                        provider="openalex",
                    )
                resp.raise_for_status()
        except ProviderThrottledError:
            raise
        except httpx.HTTPError as exc:
            raise ProviderError(f"OpenAlex search failed: {exc}") from exc
        results = resp.json().get("results", [])
        papers: list[PaperMetadata] = []
        for r in results[:limit]:
            authors = [
                a.get("author", {}).get("display_name", "")
                for a in r.get("authorships", [])
            ]
            papers.append(
                PaperMetadata(
                    title=r.get("title") or r.get("display_name") or "Untitled",
                    abstract=self._reconstruct_abstract(r.get("abstract_inverted_index")),
                    authors=[a for a in authors if a],
                    year=r.get("publication_year"),
                    doi=clean_doi(r.get("doi")),
                    venue=(r.get("primary_location") or {}).get("source", {}) and
                          ((r.get("primary_location") or {}).get("source") or {}).get("display_name"),
                    source_provider=self.name,
                    provider_id=str(r.get("id", "")).rsplit("/", 1)[-1],
                    source_url=r.get("doi") or r.get("id"),
                    citation_count=r.get("cited_by_count", 0),
                    topics=[
                        t.get("display_name", "")
                        for t in (r.get("topics") or [])[:4]
                        if t.get("display_name")
                    ],
                )
            )
        return papers

    async def get_paper(self, provider_id: str) -> PaperMetadata | None:
        try:
            async with httpx.AsyncClient(timeout=settings.literature_timeout_seconds) as client:
                resp = await client.get(f"{BASE_URL}/works/{provider_id}", params=self._params())
                if resp.status_code == 404:
                    return None
                resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise ProviderError(f"OpenAlex get_paper failed: {exc}") from exc
        r = resp.json()
        return PaperMetadata(
            title=r.get("title") or "Untitled",
            abstract=self._reconstruct_abstract(r.get("abstract_inverted_index")),
            doi=clean_doi(r.get("doi")),
            year=r.get("publication_year"),
            source_provider=self.name,
            provider_id=provider_id,
            source_url=r.get("doi") or r.get("id"),
        )

    @staticmethod
    def _reconstruct_abstract(inverted_index: dict | None) -> str | None:
        """OpenAlex stores abstracts as inverted index — rebuild the text."""
        if not inverted_index:
            return None
        positions: list[tuple[int, str]] = []
        for word, idxs in inverted_index.items():
            for i in idxs:
                positions.append((i, word))
        positions.sort()
        return " ".join(w for _, w in positions) or None
