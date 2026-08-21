"""FastAPI application entrypoint."""
from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import api_router
from app.core.config import settings
from app.core.exceptions import AppError
from app.core.logging import configure_logging, get_logger, request_id_var, user_id_var
from app.db.base import Base
from app.db.database import SessionLocal, engine
from app.db.models import AuditLog

logger = get_logger("app")

# Simple in-memory sliding-window rate limiter (per IP)
_rate_buckets: dict[str, list[float]] = {}


class WorkerHandle:
    """Manages the embedded background worker task."""

    def __init__(self) -> None:
        self.task = None
        self.shutdown = None

    def start(self) -> None:
        if not settings.run_worker_in_app:
            return
        from app.workers.worker import worker_loop

        self.shutdown = __import__("asyncio").Event()
        self.task = __import__("asyncio").get_event_loop().create_task(worker_loop(self.shutdown))
        logger.info("worker.embedded_started")

    async def stop(self) -> None:
        if self.shutdown is not None:
            self.shutdown.set()
        if self.task is not None:
            try:
                await asyncio_wait_for(self.task, timeout=5)
            except Exception:  # pragma: no cover
                self.task.cancel()


async def asyncio_wait_for(task, timeout):  # type: ignore[no-untyped-def]
    import asyncio

    try:
        await asyncio.wait_for(asyncio.shield(task), timeout=timeout)
    except TimeoutError:
        pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging("DEBUG" if settings.is_development else "INFO")
    _ensure_fts_table()
    worker = WorkerHandle()
    worker.start()
    logger.info(
        "app.started",
        env=settings.app_env,
        mock_mode=settings.mock_mode,
        llm_provider=("mock" if settings.is_mock_llm else settings.llm_provider),
    )
    yield
    await worker.stop()
    engine.dispose()


def _ensure_fts_table() -> None:
    """Create the FTS5 virtual table if SQLite supports it (graceful fallback)."""
    from sqlalchemy import text

    with engine.begin() as conn:
        try:
            conn.execute(
                text(
                    "CREATE VIRTUAL TABLE IF NOT EXISTS papers_fts USING fts5("
                    "paper_id UNINDEXED, title, abstract)"
                )
            )
        except Exception as exc:  # pragma: no cover - FTS5 unavailable
            logger.warning("fts5.unavailable", error=str(exc)[:120])


app = FastAPI(
    title="ResearchCollision API",
    description=(
        "AI Research Collaboration & Research Intersection Discovery Agent. "
        "Evidence-aware discovery of research intersections and collaboration opportunities."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
    """Request ID + structured access log + rate limiting."""
    rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
    request_id_var.set(rid)

    # rate limiting (skip health/docs)
    path = request.url.path
    if not path.startswith(("/health", "/docs", "/openapi.json", "/redoc")):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        bucket = _rate_buckets.setdefault(client_ip, [])
        bucket[:] = [t for t in bucket if now - t < 60]
        if len(bucket) >= settings.rate_limit_requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again shortly."},
            )
        bucket.append(now)

    started = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - started) * 1000, 1)
    logger.info(
        "http.request",
        method=request.method,
        path=path,
        status=response.status_code,
        duration_ms=duration_ms,
    )
    response.headers["x-request-id"] = rid
    return response


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):  # type: ignore[no-untyped-def]
    logger.warning("app.error", code=exc.code, message=exc.message, path=request.url.path)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):  # type: ignore[no-untyped-def]
    logger.error("app.unhandled_error", path=request.url.path, error=str(exc)[:300])
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "internal_error", "message": "Internal server error"}},
    )


@app.get("/health", tags=["health"])
def health() -> dict:
    return {
        "status": "ok",
        "app_env": settings.app_env,
        "mock_mode": settings.mock_mode,
        "time": time.time(),
    }


app.include_router(api_router, prefix="/api/v1")


def audit(user_id: str | None, action: str, **meta) -> None:  # type: ignore[no-untyped-def]
    """Persist an audit record in its own short-lived session."""
    db = SessionLocal()
    try:
        db.add(AuditLog(user_id=user_id, action=action, meta=meta or None))
        db.commit()
    except Exception:  # pragma: no cover
        db.rollback()
    finally:
        db.close()
