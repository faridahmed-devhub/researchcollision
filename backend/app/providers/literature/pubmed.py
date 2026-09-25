"""PubMed literature provider via NCBI E-utilities (esearch + efetch).

Public API; no key required (NCBI recommends an API key). Without a key the
provider self-throttles to 3 requests/second as required by NCBI guidelines.
Only MEDLINE/PubMed records marked as having an abstract are returned, so each
record is usable as evidence text. ``provider_id`` is the PMID. PubMed efetch
XML is namespace-less; parsing is namespace-agnostic.
"""
from __future__ import annotations

import asyncio
import re
import xml.etree.ElementTree as ET
from html import unescape
from typing import Any

import httpx
import structlog

from app.core.config import settings
from app.core.exceptions import ProviderError
from app.providers.literature.base import PaperMetadata, clean_doi

logger = structlog.get_logger(__name__)
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
BASE_URL = f"{EUTILS}/esearch.fcgi"
FETCH_URL = f"{EUTILS}/efetch.fcgi"

MIN_INTERVAL = 0.35  # >=3 req/s without an API key (NCBI guideline)

# Block undesired publication types so records are citable articles/reviews, not
# errata or commentaries that a keyword baseline would treat as evidence.
BLOCKED_PUBTYPES = (
    "Retracted Publication",
    "Retraction of Publication",
    "Comment",
    "Letter",
    "Editorial",
    "Published Erratum",
)


def _ns(root: ET.Element) -> str:
    return root.tag[: root.tag.rfind("}") + 1] if root.tag.startswith("{") else ""


def _eutils_params(extra: dict[str, str] | None = None) -> dict[str, str]:
    params: dict[str, str] = {"retmode": "json"}
    if extra:
        params.update(extra)
    if settings.ncbi_email:
        params["tool"] = "researchcollision"
        params["email"] = settings.ncbi_email
    return params


class PubmedProvider:
    name = "pubmed"

    def __init__(self, *, max_concurrent: int = 1) -> None:
        self._sem = asyncio.Semaphore(max_concurrent)
        self._last_request = 0.0

    async def _throttled_get(self, client: httpx.AsyncClient, url: str, params: dict[str, str]) -> httpx.Response:
        async with self._sem:
            wait = MIN_INTERVAL - (asyncio.get_event_loop().time() - self._last_request)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_request = asyncio.get_event_loop().time()
            resp = await client.get(url, params=params)
            _maybe_raise_http(resp)
            return resp

    async def search(self, query: str, *, limit: int = 10) -> list[PaperMetadata]:
        async with httpx.AsyncClient(timeout=settings.literature_timeout_seconds) as client:
            term = _translate_search_query(query)
            term = f"{term} AND hasabstract[text] AND english[language]"
            esearch = await self._throttled_get(
                client,
                BASE_URL,
                _eutils_params(
                    {
                        "db": "pubmed",
                        "term": term,
                        "retmax": str(min(limit * 3, 50)),
                        "sort": "relevance",
                        "retmode": "json",
                    }
                ),
            )
            body = esearch.json()
            idlist = (body.get("esearchresult") or {}).get("idlist", [])
            if not idlist:
                return []
            return await self._fetch_records(client, idlist[:limit])

    async def get_paper(self, provider_id: str) -> PaperMetadata | None:
        async with httpx.AsyncClient(timeout=settings.literature_timeout_seconds) as client:
            papers = await self._fetch_records(client, [provider_id])
        return papers[0] if papers else None

    async def _fetch_records(self, client: httpx.AsyncClient, ids: list[str]) -> list[PaperMetadata]:
        efetch = await self._throttled_get(
            client,
            FETCH_URL,
            _eutils_params(
                {
                    "db": "pubmed",
                    "id": ",".join(ids),
                    "retmode": "xml",
                    "rettype": "abstract",
                }
            ),
        )
        root = ET.fromstring(efetch.text)
        ns = _ns(root)
        out: list[PaperMetadata] = []
        for art in root:
            if art.tag != f"{ns}PubmedArticle":
                continue
            citation = art.find(f"{ns}MedlineCitation")
            pmid = citation.findtext(f"{ns}PMID") if citation is not None else None
            paper = _parse_article(art, ns, pmid or "")
            if paper is not None:
                out.append(paper)
        return out


def _translate_search_query(query: str) -> str:
    """Build a safe NCBI boolean query from a free-text query string.

    Each whitespace-separated token is quoted, then AND-joined so the query
    targets the domain literature (PubMed then ranks by relevance), mirroring
    the all-terms behavior of OpenAlex `search`.
    """
    parts = [f'"{t}"' for t in re.split(r"\s+", query.strip()) if t]
    return " AND ".join(parts) if parts else query


def _maybe_raise_http(resp: httpx.Response) -> None:
    if resp.status_code >= 400:
        raise ProviderError(f"PubMed E-utilities HTTP {resp.status_code}: {resp.text[:200]}")


def _parse_article(art: ET.Element, ns: str, pmid: str) -> PaperMetadata | None:
    citation = art.find(f"{ns}MedlineCitation")
    if citation is None:
        return None

    def _gettext(*path: str) -> str | None:
        node: Any = citation
        for part in path:
            node = node.find(f"{ns}{part}") if isinstance(node, ET.Element) else None
        if isinstance(node, ET.Element) and node.text:
            return node.text.strip()
        return None

    title = _gettext("Article", "ArticleTitle")
    abstract = "\n".join(
        t.text.strip()
        for t in citation.findall(f"{ns}Article/{ns}Abstract/{ns}AbstractText")
        if t.text
    ) or None

    pubtypes = [
        t.text
        for t in citation.findall(f"{ns}Article/{ns}PublicationTypeList/{ns}PublicationType")
        if t.text
    ]
    if any(pt.strip().lower() in (b.lower() for b in BLOCKED_PUBTYPES) for pt in pubtypes):
        return None
    if not abstract:
        return None
    if not title:
        title = "Untitled"

    authors = [
        (a.findtext(f"{ns}LastName") or "")
        + (" " + a.findtext(f"{ns}Initials") if a.findtext(f"{ns}Initials") else "")
        for a in citation.findall(f"{ns}Article/{ns}AuthorList/{ns}Author")
    ]
    authors = [a.strip() for a in authors if a.strip()]

    year = _year_from(
        citation.find(f"{ns}Article/{ns}Journal/{ns}JournalIssue/{ns}PubDate")
    )

    doi = clean_doi(unescape(_gettext("Article", "ELocationID") or ""))
    if not doi:
        for el in citation.findall(f"{ns}Article/{ns}ELocationID"):
            if (el.get("EIdType") == "doi") and el.text:
                doi = clean_doi(unescape(el.text))
                break

    return PaperMetadata(
        title=unescape(title),
        abstract=unescape(abstract)[:1500],
        authors=authors,
        year=year,
        doi=doi,
        venue=_gettext("Article", "Journal", "Title") or None,
        source_provider="pubmed",
        provider_id=pmid,
        source_url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        citation_count=0,
        topics=[],
        external_ids={"pmid": pmid},
    )


def _year_from(pubdate: ET.Element | None) -> int | None:
    if pubdate is None:
        return None
    for tag in ("Year", "MedlineDate"):
        t = pubdate.findtext(f"{tag}")
        if t:
            m = re.search(r"\d{4}", t)
            if m:
                return int(m.group())
    return None