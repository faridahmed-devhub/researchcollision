"""OpenAI-compatible chat-completions client (also base for OpenRouter)."""
from __future__ import annotations

import json
import re
from typing import Any

import httpx
import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings
from app.core.exceptions import ProviderError
from app.providers.llm.base import LLMResponse

logger = structlog.get_logger(__name__)

JSON_INSTRUCTION = (
    "You are a precise research-analysis engine. Respond with ONLY a single JSON object "
    "that validates against this JSON schema (no markdown, no commentary):\n{schema}\n"
    "Ground every claim in the provided input data. Never invent papers, authors, DOIs, "
    "URLs, or datasets. If evidence is missing, say so explicitly."
)


def extract_json_object(text: str) -> dict[str, Any]:
    """Extract the first balanced JSON object from an LLM response."""
    cleaned = re.sub(r"```(?:json)?", "", text or "").strip()
    start = cleaned.find("{")
    if start == -1:
        raise ProviderError("LLM response contained no JSON object")
    depth = 0
    for i in range(start, len(cleaned)):
        ch = cleaned[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(cleaned[start : i + 1])
                except json.JSONDecodeError as exc:
                    raise ProviderError(f"Invalid JSON from LLM: {exc}") from exc
    raise ProviderError("Unbalanced JSON in LLM response")


class OpenAICompatibleProvider:
    """Works with any OpenAI-compatible /chat/completions endpoint."""

    name = "openai_compatible"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.llm_model or "gpt-4o-mini"
        self.base_url = (base_url or settings.openai_base_url).rstrip("/")

    @retry(
        retry=retry_if_exception_type((httpx.HTTPError, ProviderError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=15),
        reraise=True,
    )
    async def _chat(self, messages: list[dict[str, str]], temperature: float, max_tokens: int) -> LLMResponse:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        async with httpx.AsyncClient(timeout=settings.literature_timeout_seconds * 2) as client:
            resp = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return LLMResponse(content=content, model=self.model, provider=self.name, usage=usage)

    async def generate(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.2,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        return await self._chat(messages, temperature, max_tokens)

    async def structured_generate(
        self,
        *,
        task: str,
        input_data: dict[str, Any],
        schema_name: str,
        schema: dict[str, Any],
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        messages = [
            {"role": "system", "content": JSON_INSTRUCTION.format(schema=json.dumps(schema))},
            {
                "role": "user",
                "content": f"Task: {task}\nInput data (JSON):\n{json.dumps(input_data, default=str)}",
            },
        ]
        last_error: Exception | None = None
        for attempt in range(3):
            response = await self._chat(messages, temperature, 2000)
            try:
                parsed = extract_json_object(response.content)
                logger.info("llm.structured_ok", task=task, attempt=attempt + 1)
                return parsed
            except ProviderError as exc:
                last_error = exc
                messages.append({"role": "assistant", "content": response.content[:500]})
                messages.append({
                    "role": "user",
                    "content": "That was not valid JSON per the schema. Respond again with ONLY valid JSON.",
                })
        raise last_error or ProviderError("structured_generate failed")
