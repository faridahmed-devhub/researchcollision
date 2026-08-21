"""User repository."""
from __future__ import annotations

from sqlalchemy import func, select

from app.db.models import User
from app.db.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(func.lower(User.email) == email.lower()))

    def create(self, email: str, password_hash: str, name: str) -> User:
        return self.add(User(email=email.lower(), password_hash=password_hash, name=name))
