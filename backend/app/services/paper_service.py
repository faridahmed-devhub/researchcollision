"""Paper service: dedup upsert, authors, taxonomy links, chunks, FTS index."""
from __future__ import annotations

import hashlib

import structlog
from sqlalchemy import text as sql_text
from sqlalchemy.orm import Session

from app.db.models import (
    DatasetEntity,
    Method,
    Paper,
    PaperAuthor,
    PaperDataset,
    PaperMethod,
    PaperTopic,
    Topic,
)
from app.db.repositories.paper_repository import normalized_title_hash
from app.providers.literature.base import PaperMetadata

logger = structlog.get_logger(__name__)


def _slug(name: str) -> str:
    import re

    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:200]


class PaperService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # -- taxonomy ----------------------------------------------------------

    def _get_or_create(self, model, name: str):
        slug = _slug(name)
        obj = self.db.query(model).filter(model.slug == slug).first()
        if obj is None:
            obj = model(name=name.strip()[:200], slug=slug)
            self.db.add(obj)
            self.db.flush()
        return obj

    def link_topics(self, paper_id: str, names: list[str]) -> None:
        for n in dict.fromkeys(names[:8]):
            if not n or len(n) > 190:
                continue
            t = self._get_or_create(Topic, n)
            exists = self.db.get(PaperTopic, f"{paper_id}:{t.id}")
            if exists is None:
                self.db.add(PaperTopic(id=f"{paper_id}:{t.id}", paper_id=paper_id, topic_id=t.id))
        self.db.flush()

    def link_methods(self, paper_id: str, names: list[str]) -> None:
        for n in dict.fromkeys(names[:8]):
            if not n or len(n) > 190:
                continue
            m = self._get_or_create(Method, n)
            exists = self.db.get(PaperMethod, f"{paper_id}:{m.id}")
            if exists is None:
                self.db.add(PaperMethod(id=f"{paper_id}:{m.id}", paper_id=paper_id, method_id=m.id))
        self.db.flush()

    def link_datasets(self, paper_id: str, names: list[str]) -> None:
        for n in dict.fromkeys(names[:6]):
            if not n or len(n) > 190:
                continue
            d = self._get_or_create(DatasetEntity, n)
            exists = self.db.get(PaperDataset, f"{paper_id}:{d.id}")
            if exists is None:
                self.db.add(PaperDataset(id=f"{paper_id}:{d.id}", paper_id=paper_id, dataset_id=d.id))
        self.db.flush()

    # -- dedup upsert -------------------------------------------------------

    def upsert_from_metadata(self, meta: PaperMetadata) -> tuple[Paper, bool]:
        """Insert or update a paper. Returns (paper, created).

        Dedup precedence: DOI > provider ID > normalized title hash.
        """
        from sqlalchemy import select

        t_hash = normalized_title_hash(meta.title)
        repo_query = select(Paper)
        paper = None
        if meta.doi:
            paper = self.db.scalar(select(Paper).where(Paper.doi == meta.doi.lower()))
        if paper is None and meta.provider_id:
            paper = self.db.scalar(
                select(Paper).where(
                    Paper.source_provider == meta.source_provider,
                    Paper.provider_id == meta.provider_id,
                )
            )
        if paper is None:
            paper = self.db.scalar(select(Paper).where(Paper.normalized_title_hash == t_hash))

        created = False
        if paper is None:
            paper = Paper(
                doi=meta.doi.lower() if meta.doi else None,
                title=meta.title,
                normalized_title_hash=t_hash,
                abstract=meta.abstract,
                publication_year=meta.year,
                venue=meta.venue,
                source_provider=meta.source_provider,
                provider_id=meta.provider_id or t_hash[:40],
                source_url=meta.source_url,
                citation_count=meta.citation_count,
                external_ids=meta.external_ids,
                is_synthetic=meta.is_synthetic,
            )
            self.db.add(paper)
            self.db.flush()
            created = True
        else:
            # enrich missing fields
            if not paper.abstract and meta.abstract:
                paper.abstract = meta.abstract
            if not paper.doi and meta.doi:
                paper.doi = meta.doi.lower()
            if meta.topics:
                self.link_topics(paper.id, meta.topics)

        # authors
        if meta.authors:
            existing = {
                (pa.author_name or "").lower()
                for pa in self.db.query(PaperAuthor).filter(PaperAuthor.paper_id == paper.id)
            }
            for pos, name in enumerate(meta.authors[:25]):
                if name and name.lower() not in existing:
                    self.db.add(
                        PaperAuthor(paper_id=paper.id, author_name=name, position=pos)
                    )
            self.db.flush()

        if meta.topics:
            self.link_topics(paper.id, meta.topics)
        self._update_fts(paper)
        return paper, created

    # -- FTS -----------------------------------------------------------------

    def _update_fts(self, paper: Paper) -> None:
        try:
            self.db.execute(
                sql_text("DELETE FROM papers_fts WHERE paper_id = :pid"),
                {"pid": paper.id},
            )
            self.db.execute(
                sql_text(
                    "INSERT INTO papers_fts (paper_id, title, abstract) VALUES (:pid, :t, :a)"
                ),
                {"pid": paper.id, "t": paper.title or "", "a": (paper.abstract or "")[:8000]},
            )
        except Exception as exc:  # FTS table may not exist yet
            logger.debug("fts.update_skipped", error=str(exc)[:120])

    # -- chunking --------------------------------------------------------------

    def make_chunks(self, text: str, target_chars: int = 900) -> list[str]:
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks: list[str] = []
        buf = ""
        for p in paragraphs:
            if len(buf) + len(p) + 1 <= target_chars:
                buf = f"{buf}\n{p}".strip()
            else:
                if buf:
                    chunks.append(buf)
                buf = p[:target_chars]
        if buf:
            chunks.append(buf)
        return chunks or ([text[:target_chars]] if text else [])

    @staticmethod
    def content_hash(*parts: str) -> str:
        return hashlib.sha256("||".join(parts).encode("utf-8")).hexdigest()
