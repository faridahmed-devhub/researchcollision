"""API dependencies: current user + workspace authorization."""
from __future__ import annotations

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError, AuthorizationError, NotFoundError
from app.core.security import decode_access_token
from app.db.database import get_db
from app.db.models import User, Workspace


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise AuthenticationError("Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    user_id = decode_access_token(token)
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise AuthenticationError("User not found or inactive")
    return user


def get_owned_workspace(
    workspace_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Workspace:
    """Workspace authorization: one user can never access another's workspace."""
    ws = db.get(Workspace, workspace_id)
    if ws is None:
        raise NotFoundError("Workspace not found")
    if ws.user_id != user.id:
        raise AuthorizationError("You do not have access to this workspace")
    return ws
