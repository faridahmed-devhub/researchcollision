"""Literature service: cached search over the provider chain."""
from __future__ import annotations

import time

import structlog

from app.providers.literature.base import PaperMetadata
from app.providers.literature.factory import LiteratureProviderChain

logger = structlog.get_logger(__name__)

_TTL_SECONDS = 3600


class LiteratureService:
    """In-memory TTL cache keyed by (query, limit). Content-hash friendly."""

    def __init__(self, chain: LiteratureProviderChain | None = None) -> None:
        self.chain = chain or LiteratureProviderChain()
        self._cache: dict[str, tuple[float, list[PaperMetadata], str]] = {}

    async def search(self, query: str, *, limit: int = 10, refresh: bool = False) -> tuple[list[PaperMetadata], str]:
        key = f"{query.strip().lower()}::{limit}"
        if not refresh:
            hit = self._cache.get(key)
            if hit and time.time() - hit[0] < _TTL_SECONDS:
                return hit[1], hit[2]
        papers, provider = await self.chain.search(query, limit=limit)
        self._cache[key] = (time.time(), papers, provider)
        return papers, provider
