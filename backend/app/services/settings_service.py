"""Settings service: key/value store for configurable behavior."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import DEFAULT_COLLABORATION_WEIGHTS
from app.db.models import Setting


class SettingsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, key: str, default: dict | None = None) -> dict:
        row = self.db.scalar(select(Setting).where(Setting.key == key))
        if row is None:
            return default if default is not None else {}
        return row.value or {}

    def set(self, key: str, value: dict) -> None:
        row = self.db.scalar(select(Setting).where(Setting.key == key))
        if row is None:
            self.db.add(Setting(key=key, value=value))
        else:
            row.value = value
        self.db.flush()

    def collaboration_weights(self) -> dict[str, float]:
        stored = self.get("collaboration_weights", {})
        weights = {**DEFAULT_COLLABORATION_WEIGHTS}
        for k in weights:
            v = stored.get(k)
            if isinstance(v, (int, float)) and 0 < float(v) <= 1:
                weights[k] = float(v)
        return weights
