"""arXiv literature provider (public Atom API).

The export API is frequently rate-limited (429) or slow (read timeouts), so the
provider retries with exponential backoff for transient failures and sends a
descriptive User-Agent per arXiv's etiquette.
"""
from __future__ import annotations

import asyncio
import re
import xml.etree.ElementTree as ET

import httpx
import structlog

from app.core.config import settings
from app.core.exceptions import ProviderError
from app.providers.literature.base import PaperMetadata, clean_doi

logger = structlog.get_logger(__name__)
BASE_URL = "https://export.arxiv.org/api/query"
NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
MAX_ATTEMPTS = 3
RETRY_BASE = 1.0
RETRY_MAX = 4.0
RETRYABLE = {429, 500, 502, 503, 504}


class ArxivProvider:
    name = "arxiv"

    async def search(self, query: str, *, limit: int = 10) -> list[PaperMetadata]:
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": min(limit, 50),
        }
        text = await self._get_with_retry(params)
        return self._parse(text)

    async def get_paper(self, provider_id: str) -> PaperMetadata | None:
        text = await self._get_with_retry({"id_list": provider_id, "max_results": 1})
        papers = self._parse(text)
        return papers[0] if papers else None

    async def _get_with_retry(self, params: dict) -> str:
        last: Exception | None = None
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                async with httpx.AsyncClient(
                    timeout=max(settings.literature_timeout_seconds, 30.0),
                    follow_redirects=True,
                    headers=_user_agent(),
                ) as client:
                    resp = await client.get(BASE_URL, params=params)
                if resp.status_code in RETRYABLE and attempt < MAX_ATTEMPTS:
                    await asyncio.sleep(min(RETRY_BASE * (2 ** (attempt - 1)), RETRY_MAX))
                    continue
                resp.raise_for_status()
                return resp.text
            except (httpx.HTTPError, httpx.TimeoutException) as exc:
                last = exc
                if attempt < MAX_ATTEMPTS:
                    await asyncio.sleep(min(RETRY_BASE * (2 ** (attempt - 1)), RETRY_MAX))
        raise ProviderError(f"arXiv search failed: {last}") from last

    def _parse(self, xml_text: str) -> list[PaperMetadata]:
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            raise ProviderError(f"arXiv XML parse failed: {exc}") from exc
        papers = []
        for entry in root.findall("atom:entry", NS):
            arxiv_id = (entry.findtext("atom:id", "", NS) or "").rsplit("/", 1)[-1]
            arxiv_id = re.sub(r"v\d+$", "", arxiv_id)
            doi = clean_doi(entry.findtext("arxiv:doi", None, NS))
            papers.append(
                PaperMetadata(
                    title=re.sub(r"\s+", " ", entry.findtext("atom:title", "Untitled", NS)).strip(),
                    abstract=re.sub(r"\s+", " ", entry.findtext("atom:summary", "", NS)).strip() or None,
                    authors=[
                        a.findtext("atom:name", "", NS)
                        for a in entry.findall("atom:author", NS)
                    ],
                    year=int(entry.findtext("atom:published", "0", NS)[:4]) or None,
                    doi=doi,
                    venue="arXiv",
                    source_provider=self.name,
                    provider_id=arxiv_id,
                    source_url=f"https://arxiv.org/abs/{arxiv_id}",
                )
            )
        return papers


def _user_agent() -> dict[str, str]:
    # arXiv asks callers to identify themselves; reuse the configured OpenAlex
    # contact email as a neutral contact when available.
    contact = settings.openalex_email or settings.ncbi_email or settings.crossref_email
    if contact:
        return {"User-Agent": f"researchcollision-dataset-builder/0.2 (contact: {contact})"}
    return {"User-Agent": "researchcollision-dataset-builder/0.2"}