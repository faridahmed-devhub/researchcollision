"""Mock literature provider backed by clearly-marked synthetic data."""
from __future__ import annotations

from app.providers.literature.base import PaperMetadata
from app.utils.synthetic_data import SYNTHETIC_PAPERS


class MockLiteratureProvider:
    name = "mock"

    async def search(self, query: str, *, limit: int = 10) -> list[PaperMetadata]:
        q_tokens = set(query.lower().replace(",", " ").split())
        scored: list[tuple[float, dict]] = []
        for p in SYNTHETIC_PAPERS:
            text = " ".join(
                [p["title"], p["abstract"], " ".join(p["topics"]), " ".join(p["authors"])]
            ).lower()
            tokens = set(text.split())
            overlap = len(q_tokens & tokens)
            if overlap:
                scored.append((overlap, p))
        scored.sort(key=lambda t: (-t[0], t[1]["provider_id"]))
        if not scored:  # fall back to a stable subset so demo always works
            scored = [(0.0, p) for p in SYNTHETIC_PAPERS[:limit]]
        return [self._to_metadata(p) for _, p in scored[:limit]]

    async def get_paper(self, provider_id: str) -> PaperMetadata | None:
        for p in SYNTHETIC_PAPERS:
            if p["provider_id"] == provider_id:
                return self._to_metadata(p)
        return None

    @staticmethod
    def _to_metadata(p: dict) -> PaperMetadata:
        return PaperMetadata(
            title=p["title"],
            abstract=p["abstract"],
            authors=p["authors"],
            year=p["year"],
            doi=p.get("doi"),
            venue=p["venue"],
            source_provider="mock",
            provider_id=p["provider_id"],
            source_url=None,
            citation_count=p["citation_count"],
            topics=p["topics"],
            is_synthetic=True,
        )
