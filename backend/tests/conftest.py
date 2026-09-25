"""Shared fixtures: isolated temp DB, test client, auth helpers."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Force mock providers + temp DB BEFORE importing app modules.
# When the operator explicitly opts into live-provider smoke tests
# (RUN_REAL_PROVIDER_TESTS=1), keep their real LITERATURE_PROVIDER setting
# so the live tests exercise the real chain instead of mock.
if os.getenv("RUN_REAL_PROVIDER_TESTS") != "1":
    os.environ["LITERATURE_PROVIDER"] = "mock"
os.environ["LLM_PROVIDER"] = "mock"
os.environ["EMBEDDING_PROVIDER"] = "mock"
os.environ["RUN_WORKER_IN_APP"] = "false"
os.environ["SECRET_KEY"] = "test-secret-key-for-pytest-only"


@pytest.fixture()
def db_engine(tmp_path):
    from app.db.base import Base
    from app.db.database import create_db_engine, make_session_factory

    engine = create_db_engine(f"sqlite:///{tmp_path / 'test.db'}")
    # FTS table (best effort)
    try:
        from sqlalchemy import text

        with engine.begin() as conn:
            conn.execute(
                text(
                    "CREATE VIRTUAL TABLE IF NOT EXISTS papers_fts USING fts5("
                    "paper_id UNINDEXED, title, abstract)"
                )
            )
    except Exception:
        pass
    import app.db.models  # noqa: F401  (register all tables before create_all)

    Base.metadata.create_all(bind=engine)
    factory = make_session_factory(engine)
    yield engine, factory
    engine.dispose()


@pytest.fixture()
def db_session(db_engine):
    _engine, factory = db_engine
    session = factory()
    yield session
    session.close()


@pytest_asyncio.fixture()
async def client(db_engine):
    """HTTP client bound to a fresh app with the test DB session overridden."""
    from fastapi import FastAPI

    _engine, factory = db_engine

    # Import a fresh app instance (module-level app is fine; override deps)
    from app.api.dependencies import get_db
    from app.main import app as fastapi_app

    def _override_get_db():
        session = factory()
        try:
            yield session
        finally:
            session.close()

    fastapi_app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    fastapi_app.dependency_overrides.clear()


class AuthClient:
    """Convenience wrapper: registers a user and attaches the token."""

    def __init__(self, client: AsyncClient):
        self.client = client
        self.token: str | None = None
        self.user_id: str | None = None

    async def register(self, email="user@test.dev", password="password123", name="Test User"):
        r = await self.client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password, "name": name},
        )
        assert r.status_code == 201, r.text
        data = r.json()
        self.token = data["access_token"]
        self.user_id = data["user"]["id"]
        return data

    @property
    def headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}

    async def create_workspace(self, name="WS") -> dict:
        r = await self.client.post(
            "/api/v1/workspaces", json={"name": name}, headers=self.headers
        )
        assert r.status_code == 201, r.text
        return r.json()


@pytest_asyncio.fixture()
async def auth(client):
    ac = AuthClient(client)
    await ac.register()
    return ac


@pytest.fixture()
def mock_llm():
    from app.providers.llm.mock import MockLLMProvider

    return MockLLMProvider()


@pytest.fixture()
def sample_cv_text() -> str:
    return (
        "Dr. Jane Doe\n"
        "Research Scientist\n"
        "\n"
        "Research Interests:\n"
        "- machine learning for healthcare\n"
        "- time series analysis\n"
        "\n"
        "Publications:\n"
        "- 2022: Predictive Models for Patient Monitoring (Journal of Health AI)\n"
        "- 2020: Time Series Transformers for Vital Signs (Medical ML Conf)\n"
        "\n"
        "Skills:\n"
        "- Python, PyTorch, SQL\n"
        "\n"
        "Experience:\n"
        "- Senior Research Scientist, HealthLab (2020-present)\n"
    )
