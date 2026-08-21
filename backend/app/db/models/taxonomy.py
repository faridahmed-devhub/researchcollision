from __future__ import annotations

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, gen_uuid, TimestampMixin


def slugify(value: str) -> str:
    import re

    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


class Topic(TimestampMixin, Base):
    __tablename__ = "topics"
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(220), unique=True, index=True, nullable=False)


class Method(TimestampMixin, Base):
    __tablename__ = "methods"
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(220), unique=True, index=True, nullable=False)


class DatasetEntity(TimestampMixin, Base):
    __tablename__ = "datasets"
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(220), unique=True, index=True, nullable=False)


class PaperTopic(Base):
    __tablename__ = "paper_topics"
    __table_args__ = (UniqueConstraint("paper_id", "topic_id", name="uq_paper_topic"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    paper_id: Mapped[str] = mapped_column(
        ForeignKey("papers.id", ondelete="CASCADE"), index=True, nullable=False
    )
    topic_id: Mapped[int] = mapped_column(
        ForeignKey("topics.id", ondelete="CASCADE"), index=True, nullable=False
    )


class PaperMethod(Base):
    __tablename__ = "paper_methods"
    __table_args__ = (UniqueConstraint("paper_id", "method_id", name="uq_paper_method"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    paper_id: Mapped[str] = mapped_column(
        ForeignKey("papers.id", ondelete="CASCADE"), index=True, nullable=False
    )
    method_id: Mapped[int] = mapped_column(
        ForeignKey("methods.id", ondelete="CASCADE"), index=True, nullable=False
    )


class PaperDataset(Base):
    __tablename__ = "paper_datasets"
    __table_args__ = (UniqueConstraint("paper_id", "dataset_id", name="uq_paper_dataset"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    paper_id: Mapped[str] = mapped_column(
        ForeignKey("papers.id", ondelete="CASCADE"), index=True, nullable=False
    )
    dataset_id: Mapped[int] = mapped_column(
        ForeignKey("datasets.id", ondelete="CASCADE"), index=True, nullable=False
    )

