"""arXiv literature provider (public Atom API)."""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET

import httpx
import structlog

from app.core.config import settings
from app.core.exceptions import ProviderError
from app.providers.literature.base import PaperMetadata, clean_doi

logger = structlog.get_logger(__name__)
BASE_URL = "http://export.arxiv.org/api/query"
NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


class ArxivProvider:
    name = "arxiv"

    async def search(self, query: str, *, limit: int = 10) -> list[PaperMetadata]:
        try:
            async with httpx.AsyncClient(timeout=settings.literature_timeout_seconds) as client:
                resp = await client.get(
                    BASE_URL,
                    params={
                        "search_query": f"all:{query}",
                        "start": 0,
                        "max_results": min(limit, 50),
                    },
                )
                resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise ProviderError(f"arXiv search failed: {exc}") from exc
        return self._parse(resp.text)

    async def get_paper(self, provider_id: str) -> PaperMetadata | None:
        try:
            async with httpx.AsyncClient(timeout=settings.literature_timeout_seconds) as client:
                resp = await client.get(
                    BASE_URL, params={"id_list": provider_id, "max_results": 1}
                )
                resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise ProviderError(f"arXiv get_paper failed: {exc}") from exc
        papers = self._parse(resp.text)
        return papers[0] if papers else None

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
