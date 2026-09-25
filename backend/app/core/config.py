"""Application configuration loaded from environment / .env files."""
from __future__ import annotations

import secrets
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Central, typed application settings (12-factor style)."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- App ---
    app_env: str = "development"
    secret_key: str = "change-me-" + secrets.token_hex(16)
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # --- Database ---
    database_url: str = f"sqlite:///{(BACKEND_DIR / 'data' / 'researchcollision.db').as_posix()}"

    # --- LLM provider ---
    llm_provider: str = "mock"
    llm_model: str = ""
    openrouter_api_key: str = ""
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"

    # --- Literature provider ---
    literature_provider: str = "openalex"
    openalex_email: str = ""
    semantic_scholar_api_key: str = ""
    crossref_email: str = ""
    ncbi_email: str = ""

    # --- Embeddings ---
    embedding_provider: str = "mock"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # --- Limits & security ---
    max_upload_size_mb: int = 10
    access_token_expire_minutes: int = 720
    rate_limit_requests_per_minute: int = 120

    # --- Worker ---
    run_worker_in_app: bool = True
    worker_poll_interval_seconds: float = 1.0
    literature_timeout_seconds: float = 15.0

    # --- Provider tuning ---
    llm_timeout_seconds: float = 180.0
    structured_max_tokens: int = 4096
    # When False, real literature searches never silently fall back to synthetic
    # (mock) papers. The chain will instead raise and the job fails clearly.
    literature_allow_mock_fallback: bool = False

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() in {"development", "dev", "local"}

    @property
    def is_mock_llm(self) -> bool:
        """Mock mode is explicit OR when a real provider has no credentials."""
        if self.llm_provider == "mock":
            return True
        if self.llm_provider == "openrouter":
            return not self.openrouter_api_key
        if self.llm_provider == "openai_compatible":
            return not self.openai_api_key
        return False

    @property
    def is_mock_embedding(self) -> bool:
        return self.embedding_provider == "mock"

    @property
    def mock_mode(self) -> bool:
        """True when the system runs without any external AI credentials."""
        return self.is_mock_llm and self.is_mock_embedding

    @property
    def allow_synthetic_literature(self) -> bool:
        """Permit silent fallback to synthetic (mock) papers.

        Only in full mock mode (no real AI credentials configured) or when
        explicitly enabled via LITERATURE_ALLOW_MOCK_FALLBACK=true — so a
        real-provider run never silently mixes synthetic papers into results.
        """
        return self.literature_allow_mock_fallback or self.mock_mode

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
