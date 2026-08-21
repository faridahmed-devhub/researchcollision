"""Workspace repository."""
from __future__ import annotations

from sqlalchemy import select

from app.db.models import Workspace
from app.db.repositories.base_repository import BaseRepository


class WorkspaceRepository(BaseRepository[Workspace]):
    model = Workspace

    def list_for_user(self, user_id: str) -> list[Workspace]:
        return list(
            self.db.scalars(
                select(Workspace).where(Workspace.user_id == user_id).order_by(Workspace.created_at)
            )
        )

    def get_owned(self, workspace_id: str, user_id: str) -> Workspace | None:
        ws = self.get(workspace_id)
        if ws is None or ws.user_id != user_id:
            return None
        return ws
