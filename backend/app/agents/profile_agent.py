"""Profile Agent — extracts Research DNA from CV text."""
from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel

from app.agents.base import BaseAgent, OutputNormalizationError
from app.schemas.profile import ResearchDNA

RESEARCH_DNA_FIELDS = set(ResearchDNA.model_fields)

_PUB_VENUE_KEYS = ("journal", "conference", "venue", "source", "publisher")


def _canonical_publication(item: Any) -> Any:
    """Deterministically map a qwen-style publication object onto ``list[str]``.

    Observed shape: ``{"year": 2023, "title": "...", "journal"|"conference": "..."}``.
    Items that carry none of the canonical fields are returned unchanged so that
    validation rejects them loudly instead of silently converting data.
    """
    if not isinstance(item, dict):
        return item
    year = item.get("year")
    title = item.get("title")
    venue = next(
        (item[k] for k in _PUB_VENUE_KEYS if item.get(k) not in (None, "")),
        None,
    )
    parts: list[str] = []
    if year not in (None, ""):
        parts.append(str(year))
    if title not in (None, ""):
        parts.append(str(title))
    if not parts:
        return item
    text = ": ".join(parts)
    if venue is not None:
        text = f"{text} ({venue})"
    return text


def normalize_research_dna_output(raw: dict[str, Any]) -> dict[str, Any]:
    """Maps qwen-family structured output onto the ResearchDNA contract.

    Deterministically unwraps (a) a single envelope key (e.g.
    ``{"ResearchDNA": {...}}``) and (b) JSON-Schema echoes (e.g.
    ``{"properties": {...}}``) when the top level carries no expected fields,
    then normalizes publication objects to canonical strings. Outputs that map
    onto no expected field raise OutputNormalizationError — they are never
    accepted as a silently-empty ResearchDNA.
    """
    if not isinstance(raw, dict):
        raise OutputNormalizationError(
            f"ResearchDNA output is not a JSON object: {type(raw).__name__}"
        )
    candidate: dict[str, Any] = dict(raw)
    if not any(k in candidate for k in RESEARCH_DNA_FIELDS):
        extra = [k for k in candidate if k not in RESEARCH_DNA_FIELDS]
        if len(extra) == 1:
            inner = candidate[extra[0]]
            if isinstance(inner, dict) and any(k in inner for k in RESEARCH_DNA_FIELDS):
                candidate = dict(inner)
        if not any(k in candidate for k in RESEARCH_DNA_FIELDS):
            props = candidate.get("properties")
            if isinstance(props, dict) and any(k in props for k in RESEARCH_DNA_FIELDS):
                candidate = dict(props)
    if not any(k in candidate for k in RESEARCH_DNA_FIELDS):
        raise OutputNormalizationError(
            "ResearchDNA output contains no expected fields: "
            + json.dumps(raw, ensure_ascii=False)[:300]
        )
    pubs = candidate.get("publications")
    if isinstance(pubs, list):
        candidate["publications"] = [_canonical_publication(p) for p in pubs]
    return candidate


class ProfileAgent(BaseAgent):
    name = "profile_agent"
    prompt_file = "profile_extraction.txt"
    prompt_version = "v1"
    task_name = "profile_extraction"
    output_schema_name = "ResearchDNA"
    output_model = ResearchDNA

    async def extract_dna(self, cv_text: str) -> ResearchDNA:
        result: BaseModel = await self.run_structured(
            {"cv_text": cv_text[:20000]},
            normalize=normalize_research_dna_output,
        )
        return result  # type: ignore[return-value]
