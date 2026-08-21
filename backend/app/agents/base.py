"""Base agent: prompt loading, structured generation, validation, audit."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

import structlog
from pydantic import BaseModel, ValidationError

from app.core.exceptions import ProviderError
from app.providers.llm.base import AGENT_SCHEMAS, LLMProvider

logger = structlog.get_logger(__name__)

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


def compute_input_hash(input_data: dict[str, Any]) -> str:
    canonical = json.dumps(input_data, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class BaseAgent:
    """Common machinery for all agents.

    - Prompts live in agents/prompts/*.txt (never inline in code).
    - Every AI call is recorded (agent_calls table) for reproducibility.
    - Output is validated against a Pydantic schema; malformed output is
      retried once, then rejected (never persisted).
    """

    name: str = "base"
    prompt_file: str = ""
    prompt_version: str = "v1"
    task_name: str = ""
    output_schema_name: str = ""
    output_model: type[BaseModel]

    def __init__(
        self,
        llm: LLMProvider,
        *,
        db: Any | None = None,
        workspace_id: str | None = None,
        job_id: str | None = None,
    ) -> None:
        self.llm = llm
        self.db = db
        self.workspace_id = workspace_id
        self.job_id = job_id

    def load_prompt(self) -> str:
        if not self.prompt_file:
            return ""
        path = PROMPTS_DIR / self.prompt_file
        if not path.exists():
            logger.warning("agent.prompt_missing", agent=self.name, file=self.prompt_file)
            return ""
        return path.read_text(encoding="utf-8")

    def _record_call(
        self,
        input_hash: str,
        duration_ms: float,
        status: str,
        error: str | None = None,
    ) -> None:
        if self.db is None:
            return
        try:
            from app.db.models import AgentCall

            self.db.add(
                AgentCall(
                    workspace_id=self.workspace_id,
                    job_id=self.job_id,
                    agent_name=self.name,
                    prompt_version=self.prompt_version,
                    provider=getattr(self.llm, "name", "unknown"),
                    model=getattr(self.llm, "model", "unknown"),
                    input_hash=input_hash,
                    output_schema=self.output_schema_name,
                    duration_ms=duration_ms,
                    status=status,
                    error=(error or "")[:500] or None,
                )
            )
            self.db.flush()
        except Exception:  # pragma: no cover - auditing must never break jobs
            logger.warning("agent.call_record_failed", agent=self.name)

    async def run_structured(self, input_data: dict[str, Any]) -> BaseModel:
        """Generate + validate output. One retry on schema violation."""
        input_hash = compute_input_hash(input_data)
        last_error: Exception | None = None
        for attempt in range(2):
            started = time.perf_counter()
            try:
                raw = await self.llm.structured_generate(
                    task=self.task_name,
                    input_data=input_data,
                    schema_name=self.output_schema_name,
                    schema=AGENT_SCHEMAS[self.output_schema_name],
                )
                validated = self.output_model.model_validate(raw)
                self._record_call(input_hash, (time.perf_counter() - started) * 1000, "ok")
                return validated
            except (ValidationError, KeyError) as exc:
                last_error = exc
                self._record_call(
                    input_hash, (time.perf_counter() - started) * 1000, "invalid", str(exc)
                )
                logger.warning(
                    "agent.output_invalid",
                    agent=self.name,
                    attempt=attempt + 1,
                    error=str(exc)[:300],
                )
            except ProviderError as exc:
                self._record_call(
                    input_hash, (time.perf_counter() - started) * 1000, "error", str(exc)
                )
                raise
        raise ProviderError(f"Agent {self.name} produced invalid output twice: {last_error}")
