"""Evidence repository."""
from __future__ import annotations

from sqlalchemy import select

from app.db.models import Evidence
from app.db.repositories.base_repository import BaseRepository


class EvidenceRepository(BaseRepository[Evidence]):
    model = Evidence

    def for_workspace(self, workspace_id: str, limit: int = 200) -> list[Evidence]:
        return list(
            self.db.scalars(
                select(Evidence)
                .where(Evidence.workspace_id == workspace_id)
                .order_by(Evidence.created_at.desc())
                .limit(limit)
            )
        )

    def by_ids(self, ids: list[str]) -> list[Evidence]:
        if not ids:
            return []
        return list(self.db.scalars(select(Evidence).where(Evidence.id.in_(ids))))
