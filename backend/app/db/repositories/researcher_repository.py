"""Researcher repository (workspace-scoped + shared reference data)."""
from __future__ import annotations

from sqlalchemy import or_, select

from app.db.models import Researcher, ResearcherAlias
from app.db.repositories.base_repository import BaseRepository


class ResearcherRepository(BaseRepository[Researcher]):
    model = Researcher

    def search(self, query: str, workspace_id: str | None = None, limit: int = 20) -> list[Researcher]:
        """Search by name/alias. Includes shared (global) researchers."""
        like = f"%{query.strip().lower()}%"
        alias_ids = select(ResearcherAlias.researcher_id).where(
            func_lower_alias(ResearcherAlias.alias).like(like)
        )
        stmt = (
            select(Researcher)
            .where(
                or_(
                    func_lower(Researcher.name).like(like),
                    func_lower(Researcher.affiliation).like(like),
                    Researcher.id.in_(alias_ids),
                )
            )
            .limit(limit)
        )
        if workspace_id:
            # workspace-specific first, then shared reference data
            stmt = stmt.where(or_(Researcher.workspace_id == workspace_id, Researcher.workspace_id.is_(None)))
        return list(self.db.scalars(stmt))

    def get_in_workspace(self, researcher_id: str, workspace_id: str) -> Researcher | None:
        r = self.get(researcher_id)
        if r is None:
            return None
        if r.workspace_id is None or r.workspace_id == workspace_id:
            return r
        return None

    def find_by_name(self, name: str, workspace_id: str | None) -> Researcher | None:
        stmt = select(Researcher).where(func_lower(Researcher.name) == name.strip().lower())
        if workspace_id:
            stmt = stmt.where(or_(Researcher.workspace_id == workspace_id, Researcher.workspace_id.is_(None)))
        return self.db.scalar(stmt.limit(1))


def func_lower(col):  # small helper to avoid importing func everywhere
    from sqlalchemy import func

    return func.lower(col)


def func_lower_alias(col):
    return func_lower(col)
