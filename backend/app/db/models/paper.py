from __future__ import annotations

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, gen_uuid, TimestampMixin


def normalize_title(title: str) -> str:
    """Lowercase, strip non-alphanumerics â€” used for dedup hashing."""
    import re

    return re.sub(r"[^a-z0-9]+", "", title.lower())


class Paper(TimestampMixin, Base):
    """A paper record shared across workspaces (reference data).

    Deduplicated by DOI, provider ID, or normalized-title hash (service layer).
    """

    __tablename__ = "papers"

    doi: Mapped[str | None] = mapped_column(String(120), index=True, nullable=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_title_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    abstract: Mapped[str | None] = mapped_column(Text, nullable=True)
    publication_year: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    venue: Mapped[str | None] = mapped_column(String(400), nullable=True)
    source_provider: Mapped[str] = mapped_column(String(40), nullable=False)
    provider_id: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(600), nullable=True)
    citation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    external_ids: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    authors = relationship("PaperAuthor", back_populates="paper", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Paper {self.id} {self.title[:50]!r}>"


class PaperAuthor(Base):
    __tablename__ = "paper_authors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    paper_id: Mapped[str] = mapped_column(
        ForeignKey("papers.id", ondelete="CASCADE"), index=True, nullable=False
    )
    researcher_id: Mapped[str | None] = mapped_column(
        ForeignKey("researchers.id", ondelete="SET NULL"), nullable=True
    )
    author_name: Mapped[str] = mapped_column(String(300), nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    paper = relationship("Paper", back_populates="authors")
    researcher = relationship("Researcher", back_populates="authorships")

