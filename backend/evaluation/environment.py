"""Offline-safe defaults for evaluation runs.

The evaluator must work without API keys on a fresh machine. Because the app
reads provider environment variables at import time, these defaults are set
*before* any ``app.*`` module is imported.

Operators with real credentials can opt in by setting
``EVALUATION_FORCE_OFFLINE=0`` and exporting their real provider settings;
the report records which providers were actually used so results are never
presented as if they ran offline when they did not.
"""
from __future__ import annotations

import os


def configure_offline_defaults() -> None:
    """Force deterministic offline providers unless explicitly opted out."""
    if os.getenv("EVALUATION_FORCE_OFFLINE", "1") == "1":
        os.environ.setdefault("LLM_PROVIDER", "mock")
        os.environ.setdefault("EMBEDDING_PROVIDER", "mock")
        os.environ.setdefault("LITERATURE_PROVIDER", "mock")
    # Evaluation runs drive the pipeline synchronously; disable the embedded worker.
    os.environ.setdefault("RUN_WORKER_IN_APP", "false")


def offline_mode() -> bool:
    """True when the effective run is fully mock (LLM + literature).

    ``EVALUATION_FORCE_OFFLINE=1`` (or unset) forces offline. Otherwise the
    *effective* providers are read from settings, so a run that really used
    the OpenAI-style literature chain (settings ``literature_provider`` =
    ``openalex``) is reported online even if the env var is unset. A mock LLM
    with a real literature provider is NOT "offline mode" — it is a hybrid run
    and is reported as such.
    """
    if os.getenv("EVALUATION_FORCE_OFFLINE", "1") == "1":
        return True
    llm = os.getenv("LLM_PROVIDER")
    lit = os.getenv("LITERATURE_PROVIDER")
    if llm is None or lit is None:
        try:
            from app.core.config import settings
        except Exception:  # pragma: no cover - offline default must never raise
            pass
        else:
            llm = llm or settings.llm_provider
            lit = lit or settings.literature_provider
    return (llm in (None, "mock")) and (lit in (None, "mock"))