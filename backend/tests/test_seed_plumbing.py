"""Phase 2A: seed plumbing for reproducibility.

Covers:
- providers accept and forward the seed (payload plumbing for
  OpenAI-compatible endpoints; no-op semantics for the deterministic mock);
- ``get_system(name, seed=...)`` produces fresh, correctly-seeded instances;
- agents forward their seed to the LLM call;
- end-to-end: same seed + same config -> identical artifacts; different seeds
  are distinguishable exactly where the run is stochastic (blind eval ids),
  while deterministic components (mock metrics) stay identical.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import httpx
import pytest

from app.agents.base import BaseAgent
from app.providers.llm.base import LLMResponse
from app.providers.llm.mock import MockLLMProvider
from app.providers.llm.openai_compatible import OpenAICompatibleProvider

FIXTURE = Path(__file__).resolve().parents[1] / "evaluation" / "data" / "demo_discovery.json"


def _drop_durations(cases):
    """Runtime duration_ms is a non-deterministic measurement: exclude it from
    reproducibility comparisons of the (deterministic-under-mock) outputs."""
    out = []
    for case in cases:
        systems = {
            name: {k: v for k, v in run.items() if k != "duration_ms"}
            for name, run in case["systems"].items()
        }
        out.append({**case, "systems": systems})
    return out


# ---------------------------------------------------------------------------
# Provider level
# ---------------------------------------------------------------------------


async def test_mock_provider_accepts_seed_and_stays_deterministic():
    p = MockLLMProvider()
    input_data = {
        "researcher_a": {"name": "A", "bio": "x", "topics": ["ml"], "methods": ["nn"]},
        "researcher_b": {"name": "B", "bio": "y", "topics": ["ai"], "methods": ["svm"]},
    }
    schema: dict[str, Any] = {"type": "object", "properties": {}}
    r0 = await p.structured_generate(
        task="evaluation_llm_only", input_data=input_data,
        schema_name="eval_llm_only", schema=schema, seed=3,
    )
    r1 = await p.structured_generate(
        task="evaluation_llm_only", input_data=input_data,
        schema_name="eval_llm_only", schema=schema, seed=99,
    )
    assert r0 == r1  # mock ignores seed: fully deterministic
    gen0 = await p.generate([{"role": "user", "content": "hi"}], seed=1)
    assert gen0.content  # signature accepts seed without error


async def test_generate_accepts_seed():
    p = MockLLMProvider()
    resp = await p.generate([{"role": "user", "content": "hi"}], seed=7)
    assert isinstance(resp, LLMResponse)


class _FakePost:
    def __init__(self, payloads: list[dict]):
        self.payloads = payloads

    async def __call__(self, url, *, headers=None, json=None):
        self.payloads.append(json)
        return SimpleNamespace(
            status_code=200,
            json=lambda: {
                "choices": [
                    {"message": {"content": '{"ok": true}'}, "finish_reason": "stop"}
                ],
                "usage": {},
            },
        )


async def test_openai_compatible_sends_seed_when_set(monkeypatch):
    payloads: list[dict] = []
    monkeypatch.setattr(httpx.AsyncClient, "post", _FakePost(payloads))
    provider = OpenAICompatibleProvider(
        api_key="k", model="m", base_url="http://llm.test/v1"
    )
    await provider.structured_generate(
        task="t", input_data={"a": 1}, schema_name="s",
        schema={"type": "object"}, seed=42,
    )
    assert payloads and payloads[-1]["seed"] == 42
    # free-form generate also forwards it
    await provider.generate([{"role": "user", "content": "x"}], seed=7)
    assert payloads[-1]["seed"] == 7


async def test_openai_compatible_omits_seed_when_not_set(monkeypatch):
    payloads: list[dict] = []
    monkeypatch.setattr(httpx.AsyncClient, "post", _FakePost(payloads))
    provider = OpenAICompatibleProvider(
        api_key="k", model="m", base_url="http://llm.test/v1"
    )
    await provider.structured_generate(
        task="t", input_data={"a": 1}, schema_name="s", schema={"type": "object"}
    )
    assert payloads and "seed" not in payloads[-1]


# ---------------------------------------------------------------------------
# System factory level
# ---------------------------------------------------------------------------


def test_get_system_propagates_seed_and_returns_fresh_instances():
    from evaluation.baselines import DEFAULT_SYSTEMS, get_system

    for name in DEFAULT_SYSTEMS:
        a = get_system(name, seed=5)
        b = get_system(name, seed=5)
        c = get_system(name, seed=6)
        assert a.seed == 5
        assert c.seed == 6
        assert a is not b  # fresh instance, no shared mutable state

    with pytest.raises(KeyError):
        get_system("nope", seed=1)


# ---------------------------------------------------------------------------
# Agent level
# ---------------------------------------------------------------------------


class _SeedSpyLLM(MockLLMProvider):
    """Records the seed passed into every structured_generate call."""

    def __init__(self):
        super().__init__()
        self.seeds: list[int | None] = []

    async def structured_generate(self, **kwargs):
        self.seeds.append(kwargs.get("seed"))
        return await super().structured_generate(**kwargs)


def test_agent_forwards_seed_to_llm():
    from app.providers.llm.base import PaperAnalysis

    spy = _SeedSpyLLM()
    agent = BaseAgent(spy, seed=123)
    agent.output_model = PaperAnalysis
    agent.output_schema_name = "PaperAnalysis"
    agent.task_name = "paper_analysis"

    async def _go():
        return await agent.run_structured(
            {"title": "T", "abstract": "A study about machine learning.", "evidence_id": "ev1"}
        )

    result = asyncio.run(_go())
    assert result.research_problem
    assert spy.seeds and spy.seeds[-1] == 123


def test_discovery_pipeline_stores_seed():
    from app.workers.tasks.discovery_pipeline import DiscoveryPipeline

    class _Job:
        workspace_id = "ws"
        config = {}

        def __init__(self):
            self.config = {}

    pipeline = DiscoveryPipeline(db=None, job=_Job(), seed=7)
    assert pipeline.seed == 7


# ---------------------------------------------------------------------------
# End-to-end: reproducibility + distinguishability
# ---------------------------------------------------------------------------


async def test_run_evaluation_same_seed_is_reproducible(tmp_path):
    from evaluation.runner import run_evaluation

    r0 = await run_evaluation(
        dataset_path=FIXTURE, systems=["keyword", "embedding", "llm_only", "pipeline"],
        out_dir=tmp_path / "seed0a", seed=0,
    )
    r1 = await run_evaluation(
        dataset_path=FIXTURE, systems=["keyword", "embedding", "llm_only", "pipeline"],
        out_dir=tmp_path / "seed0b", seed=0,
    )
    assert r0["aggregates"] == r1["aggregates"]
    assert _drop_durations(r0["cases"]) == _drop_durations(r1["cases"])
    assert r0["blind_key"] == r1["blind_key"]
    assert r0["config"]["seed"] == r1["config"]["seed"] == 0


async def test_run_evaluation_different_seeds_distinguish_stochastic_parts(tmp_path):
    from evaluation.runner import run_evaluation

    r0 = await run_evaluation(
        dataset_path=FIXTURE, systems=["keyword", "llm_only"],
        out_dir=tmp_path / "s0", seed=0,
    )
    r1 = await run_evaluation(
        dataset_path=FIXTURE, systems=["keyword", "llm_only"],
        out_dir=tmp_path / "s1", seed=1,
    )
    # The blind evaluation ids are a seeded random shuffle: different seeds
    # MUST produce a different mapping (this is the stochastic component the
    # seed controls under mock providers).
    assert r0["blind_key"] != r1["blind_key"]
    # Deterministic mock components are untouched by the seed (runtime duration,
    # a non-deterministic measurement, is excluded from the comparison).
    assert r0["aggregates"] == r1["aggregates"]
    assert _drop_durations(r0["cases"]) == _drop_durations(r1["cases"])


async def test_run_evaluation_records_seed_in_config(tmp_path):
    from evaluation.runner import run_evaluation

    results = await run_evaluation(
        dataset_path=FIXTURE, systems=["keyword"], out_dir=tmp_path, seed=11
    )
    assert results["config"]["seed"] == 11
    persisted = json.loads((tmp_path / "results.json").read_text(encoding="utf-8"))
    assert persisted["config"]["seed"] == 11