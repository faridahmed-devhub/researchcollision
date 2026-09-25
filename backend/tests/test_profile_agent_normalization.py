"""Focused tests for the profile-agent ResearchDNA output-contract handling.

Covers the observed real-provider failure modes:
  - qwen2.5:7b deterministic publication objects (list[dict] instead of list[str])
  - qwen2.5-coder:7b {"ResearchDNA": {...}} envelope
  - schema-echo family shapes ({"properties": {...}})
  - empty/invalid output that must fail loudly (never a silent empty profile)
Validation runs against the real ResearchDNA Pydantic model; no network is used.
"""
from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from app.agents.base import OutputNormalizationError
from app.agents.profile_agent import (
    ProfileAgent,
    _canonical_publication,
    normalize_research_dna_output,
)
from app.core.exceptions import ProviderError
from app.schemas.profile import ResearchDNA


class FakeLLM:
    """Deterministic stand-in for the LLM provider."""

    name = "fake"
    model = "fake-model"

    def __init__(self, responses: list[dict[str, Any]]):
        self.responses = list(responses)

    async def structured_generate(self, **_: Any) -> dict[str, Any]:
        if not self.responses:
            raise ProviderError("fake: no responses left")
        return self.responses.pop(0)


VALID_DNA = {
    "domains": ["healthcare"],
    "research_problems": ["early sepsis prediction"],
    "methods": ["transformer models"],
    "datasets": [],
    "tools": ["Python", "PyTorch", "SQL"],
    "research_questions": [],
    "publications": ["2023: Transformer Models for ICU Monitoring (JAMIA)"],
    "technical_skills": ["Python"],
    "research_interests": ["machine learning for healthcare"],
    "emerging_interests": [],
    "experience": [],
}

PUBLICATION_OBJECTS = {
    "domains": ["healthcare", "clinical time series"],
    "research_problems": [],
    "methods": [],
    "datasets": [],
    "tools": [],
    "research_questions": [],
    "publications": [
        {"year": 2023, "title": "Transformer Models for ICU Monitoring", "journal": "JAMIA"},
        {"year": 2021, "title": "Early Sepsis Prediction", "conference": "KDD"},
    ],
    "technical_skills": [],
    "research_interests": [],
    "emerging_interests": [],
    "experience": [],
}


def _envelope(dna: dict[str, Any]) -> dict[str, Any]:
    return {"ResearchDNA": dict(dna)}


def _schema_echo(dna: dict[str, Any]) -> dict[str, Any]:
    return {
        "description": "The canonical Research DNA structure (spec \u00a713).",
        "properties": dict(dna),
        "title": "ResearchDNA",
        "type": "object",
    }


async def test_valid_research_dna_passes():
    agent = ProfileAgent(FakeLLM([VALID_DNA]))
    dna = await agent.extract_dna("...")  # text content is irrelevant for fake provider
    assert isinstance(dna, ResearchDNA)
    assert dna.domains == ["healthcare"]
    assert dna.publications == ["2023: Transformer Models for ICU Monitoring (JAMIA)"]


async def test_publications_objects_normalized_to_strings():
    agent = ProfileAgent(FakeLLM([PUBLICATION_OBJECTS]))
    dna = await agent.extract_dna("...")
    assert dna.publications == [
        "2023: Transformer Models for ICU Monitoring (JAMIA)",
        "2021: Early Sepsis Prediction (KDD)",
    ]
    assert dna.domains, "publications-only issue must not empty the rest of the profile"


async def test_envelope_output_is_unwrapped_not_accepted_empty():
    agent = ProfileAgent(FakeLLM([_envelope(PUBLICATION_OBJECTS)]))
    dna = await agent.extract_dna("...")
    assert dna.domains
    assert dna.publications == [
        "2023: Transformer Models for ICU Monitoring (JAMIA)",
        "2021: Early Sepsis Prediction (KDD)",
    ]


async def test_schema_echo_output_is_unwrapped_not_accepted_empty():
    agent = ProfileAgent(FakeLLM([_schema_echo(PUBLICATION_OBJECTS)]))
    dna = await agent.extract_dna("...")
    assert dna.domains
    assert dna.publications == [
        "2023: Transformer Models for ICU Monitoring (JAMIA)",
        "2021: Early Sepsis Prediction (KDD)",
    ]


@pytest.mark.parametrize(
    "bad",
    [
        {},
        {"ResearchDNA": {"foo": "bar"}},
        {"ResearchDNA": None},
        {"unrelated": "payload"},
        {"description": "x", "title": "ResearchDNA", "type": "object"},
    ],
)
async def test_output_without_expected_fields_fails_loudly(bad):
    agent = ProfileAgent(FakeLLM([dict(bad), dict(bad)]))
    with pytest.raises(ProviderError, match="invalid output twice"):
        await agent.extract_dna("...")


async def test_publication_object_missing_all_fields_is_not_silently_converted():
    raw = {
        "publications": [{"something": "else"}],
        "domains": ["healthcare"],
    }
    agent = ProfileAgent(FakeLLM([raw, raw]))
    with pytest.raises(ProviderError, match="invalid output twice"):
        await agent.extract_dna("...")


def test_canonical_publication_preserves_passthrough_items():
    assert _canonical_publication("plain string") == "plain string"
    assert _canonical_publication({"year": 2021, "title": "T", "conference": "KDD"}) == \
        "2021: T (KDD)"
    unresolved = {"something": "else"}
    assert _canonical_publication(unresolved) is unresolved, "unusable items must pass through"


def test_normalizer_rejects_non_object_and_contractless_output():
    with pytest.raises(OutputNormalizationError):
        normalize_research_dna_output({"ResearchDNA": {"foo": "bar"}})
    with pytest.raises(OutputNormalizationError):
        normalize_research_dna_output({})


def test_normalizer_cannot_produce_silent_empty_profile():
    # Without normalization, the schema echo would be silently accepted as an empty
    # profile (pydantic extra='ignore'). Normalization must recover the real fields
    # and push wrong-typed inner values through loud validation.
    selected = normalize_research_dna_output(_schema_echo({"publications": ["x"]}))
    assert selected == {"publications": ["x"]}
    m = ResearchDNA.model_validate(selected)
    assert m.publications == ["x"]

    bad_echo = _schema_echo({"publications": {"items": {"type": "string"}}})
    selected_bad = normalize_research_dna_output(bad_echo)
    with pytest.raises(ValidationError):
        ResearchDNA.model_validate(selected_bad)