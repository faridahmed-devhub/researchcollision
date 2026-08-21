"""Paper repository with deduplication helpers."""
from __future__ import annotations

import hashlib

from sqlalchemy import or_, select

from app.db.models import Paper
from app.db.repositories.base_repository import BaseRepository


def normalized_title_hash(title: str) -> str:
    from app.db.models.paper import normalize_title

    return hashlib.sha256(normalize_title(title).encode("utf-8")).hexdigest()


class PaperRepository(BaseRepository[Paper]):
    model = Paper

    def find_duplicate(
        self,
        *,
        doi: str | None,
        provider: str,
        provider_id: str,
        title_hash: str,
    ) -> Paper | None:
        """Dedup precedence: DOI > provider ID > normalized title hash."""
        if doi:
            found = self.db.scalar(select(Paper).where(Paper.doi == doi.lower()))
            if found:
                return found
        found = self.db.scalar(
            select(Paper).where(Paper.source_provider == provider, Paper.provider_id == provider_id)
        )
        if found:
            return found
        return self.db.scalar(select(Paper).where(Paper.normalized_title_hash == title_hash))

    def search_local(self, query: str, limit: int = 20) -> list[Paper]:
        """FTS5 search with LIKE fallback."""
        like = f"%{query.strip()}%"
        try:
            rows = self.db.execute(
                "SELECT paper_id FROM papers_fts WHERE papers_fts MATCH :q LIMIT :lim",
                {"q": query.strip(), "lim": limit},
            ).fetchall()
            if rows:
                ids = [r[0] for r in rows]
                papers = self.db.scalars(select(Paper).where(Paper.id.in_(ids))).all()
                return list(papers)
        except Exception:
            pass
        stmt = (
            select(Paper)
            .where(or_(Paper.title.ilike(like), Paper.abstract.ilike(like)))
            .limit(limit)
        )
        return list(self.db.scalars(stmt))

    def by_ids(self, ids: list[str]) -> list[Paper]:
        if not ids:
            return []
        return list(self.db.scalars(select(Paper).where(Paper.id.in_(ids))))

    def for_researcher(self, researcher_id: str) -> list[Paper]:
        from app.db.models import PaperAuthor

        stmt = (
            select(Paper)
            .join(PaperAuthor, PaperAuthor.paper_id == Paper.id)
            .where(PaperAuthor.researcher_id == researcher_id)
            .order_by(Paper.publication_year.desc().nullslast())
        )
        return list(self.db.scalars(stmt))
