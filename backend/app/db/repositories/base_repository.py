"""Generic repository with common CRUD operations."""
from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """Thin data-access layer. Services depend on these, never on raw queries."""

    model: type[T]

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, entity_id: str) -> T | None:
        return self.db.get(self.model, entity_id)

    def list(self, *conditions: Any, limit: int | None = None, offset: int = 0) -> list[T]:
        stmt = select(self.model)
        for cond in conditions:
            stmt = stmt.where(cond)
        stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        return list(self.db.scalars(stmt))

    def add(self, obj: T) -> T:
        self.db.add(obj)
        self.db.flush()
        self.db.refresh(obj)
        return obj

    def update_fields(self, obj: T, **fields: Any) -> T:
        for key, value in fields.items():
            setattr(obj, key, value)
        self.db.flush()
        self.db.refresh(obj)
        return obj

    def delete(self, obj: T) -> None:
        self.db.delete(obj)
        self.db.flush()

    def count(self, *conditions: Any) -> int:
        from sqlalchemy import func as sa_func

        stmt = select(sa_func.count()).select_from(self.model)
        for cond in conditions:
            stmt = stmt.where(cond)
        return int(self.db.scalar(stmt) or 0)
