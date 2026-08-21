"""Structured logging configuration using structlog.

Never log passwords, API keys, or full CV contents.
"""
from __future__ import annotations

import logging
import sys
from contextvars import ContextVar

import structlog

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")
user_id_var: ContextVar[str] = ContextVar("user_id", default="-")
workspace_id_var: ContextVar[str] = ContextVar("workspace_id", default="-")
job_id_var: ContextVar[str] = ContextVar("job_id", default="-")


def _inject_context(
    logger: structlog.types.Logger,
    method_name: str,
    event_dict: structlog.types.EventDict,
) -> structlog.types.EventDict:
    event_dict["request_id"] = request_id_var.get()
    uid = user_id_var.get()
    wid = workspace_id_var.get()
    jid = job_id_var.get()
    if uid != "-":
        event_dict["user_id"] = uid
    if wid != "-":
        event_dict["workspace_id"] = wid
    if jid != "-":
        event_dict["job_id"] = jid
    return event_dict


def configure_logging(level: str = "INFO") -> None:
    """Configure structlog + stdlib logging once at startup."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=log_level)
    for noisy in ("httpx", "httpcore", "alembic"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            _inject_context,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(colors=True),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)


logger = get_logger("app")
