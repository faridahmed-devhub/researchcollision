"""Health check script: DB, tables, providers, FTS.

Usage: cd backend && python ../scripts/health_check.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from sqlalchemy import inspect, text  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.db.database import engine  # noqa: E402
from app.db.models import Base  # noqa: E402
import app.db.models  # noqa: F401,E402


def main() -> int:
    ok = True
    print("== ResearchCollision health check ==")
    print(f"APP_ENV: {settings.app_env}")
    print(f"LLM provider: {settings.llm_provider} (mock={settings.is_mock_llm})")
    print(f"Embedding provider: {settings.embedding_provider}")
    print(f"Literature provider: {settings.literature_provider}")

    try:
        conn = engine.connect()
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        expected = set(Base.metadata.tables)
        missing = expected - tables
        if missing:
            print(f"FAIL: missing tables: {sorted(missing)}")
            ok = False
        else:
            print(f"DB OK — {len(tables)} tables present")
        try:
            conn.execute(text("SELECT 1 FROM papers_fts LIMIT 1"))
            print("FTS5 index OK")
        except Exception:
            print("FTS5 unavailable (LIKE fallback will be used)")
        conn.close()
    except Exception as exc:
        print(f"FAIL: database error: {exc}")
        ok = False

    print("HEALTH:", "OK" if ok else "DEGRADED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
