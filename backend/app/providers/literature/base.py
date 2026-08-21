"""Literature provider interface and shared metadata type."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class PaperMetadata:
    """Normalized paper metadata returned by every provider."""

    title: str
    abstract: str | None = None
    authors: list[str] = field(default_factory=list)
    year: int | None = None
    doi: str | None = None
    venue: str | None = None
    source_provider: str = "unknown"
    provider_id: str = ""
    source_url: str | None = None
    citation_count: int = 0
    topics: list[str] = field(default_factory=list)
    external_ids: dict[str, Any] = field(default_factory=dict)
    is_synthetic: bool = False


@runtime_checkable
class LiteratureProvider(Protocol):
    name: str

    async def search(self, query: str, *, limit: int = 10) -> list[PaperMetadata]: ...

    async def get_paper(self, provider_id: str) -> PaperMetadata | None: ...


def clean_doi(doi: str | None) -> str | None:
    if not doi:
        return None
    d = doi.strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi.org/"):
        if d.startswith(prefix):
            d = d[len(prefix):]
    return d or None
