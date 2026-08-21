"""Literature provider registry with automatic fallback chain."""
from __future__ import annotations

import structlog

from app.core.config import settings
from app.core.exceptions import ProviderError
from app.providers.literature.arxiv import ArxivProvider
from app.providers.literature.base import LiteratureProvider, PaperMetadata
from app.providers.literature.crossref import CrossrefProvider
from app.providers.literature.mock import MockLiteratureProvider
from app.providers.literature.openalex import OpenAlexProvider
from app.providers.literature.semantic_scholar import SemanticScholarProvider

logger = structlog.get_logger(__name__)

_FALLBACK_ORDER = ["openalex", "semantic_scholar", "crossref", "arxiv", "mock"]


def _instantiate(name: str) -> LiteratureProvider:
    if name == "openalex":
        return OpenAlexProvider()
    if name == "semantic_scholar":
        return SemanticScholarProvider()
    if name == "crossref":
        return CrossrefProvider()
    if name == "arxiv":
        return ArxivProvider()
    if name == "mock":
        return MockLiteratureProvider()
    raise ProviderError(f"Unknown literature provider: {name}")


class LiteratureProviderChain:
    """Tries the configured provider, then falls back in a fixed order.

    Never floods APIs: one attempt per provider per call, with the shared
    timeout from settings. Network failures degrade to the mock provider so
    local development always works.
    """

    def __init__(self, primary: str | None = None) -> None:
        self.primary_name = primary or settings.literature_provider
        order = [self.primary_name] + [n for n in _FALLBACK_ORDER if n != self.primary_name]
        self.chain: list[LiteratureProvider] = []
        for n in order:
            try:
                self.chain.append(_instantiate(n))
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("literature.provider_init_failed", provider=n, error=str(exc))

    async def search(self, query: str, *, limit: int = 10) -> tuple[list[PaperMetadata], str]:
        """Returns (papers, provider_used)."""
        errors: list[str] = []
        for provider in self.chain:
            try:
                papers = await provider.search(query, limit=limit)
                if papers:
                    return papers, provider.name
            except Exception as exc:
                errors.append(f"{provider.name}: {exc}")
                logger.warning("literature.search_failed", provider=provider.name, error=str(exc))
        raise ProviderError(f"All literature providers failed: {'; '.join(errors)}")

    async def get_paper(self, provider_id: str) -> PaperMetadata | None:
        for provider in self.chain:
            try:
                paper = await provider.get_paper(provider_id)
                if paper:
                    return paper
            except Exception as exc:
                logger.warning("literature.get_failed", provider=provider.name, error=str(exc))
        return None


def get_literature_chain() -> LiteratureProviderChain:
    return LiteratureProviderChain()
