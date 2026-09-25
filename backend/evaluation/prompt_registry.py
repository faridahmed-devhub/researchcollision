"""Prompt version registry (shared by experiment persistence and prompt archive).

Maps each production prompt file to the agent that serves it and its declared
``prompt_version``. ``experiment_design.txt`` is served by HypothesisAgent at
runtime (it swaps ``prompt_file``), so it inherits the hypothesis agent's
version. Files present in ``app/agents/prompts/`` but not loaded by any agent
are reported as ``unused``.
"""
from __future__ import annotations

import importlib

from app.agents.base import BaseAgent

_AGENT_MODULES = (
    "paper_analysis_agent",
    "trajectory_agent",
    "gap_agent",
    "intersection_agent",
    "hypothesis_agent",
    "profile_agent",
    "paper_writer_agent",
)


def agent_prompt_versions() -> dict[str, dict[str, str]]:
    """Return {prompt_file: {"version": str, "agent": str}}."""
    from app.agents.base import PROMPTS_DIR

    registry: dict[str, dict[str, str]] = {}
    for modname in _AGENT_MODULES:
        try:
            mod = importlib.import_module(f"app.agents.{modname}")
        except Exception:  # pragma: no cover - registry must never break runs
            continue
        for attr in vars(mod).values():
            if isinstance(attr, type) and issubclass(attr, BaseAgent) and attr is not BaseAgent:
                prompt_file = getattr(attr, "prompt_file", None)
                if prompt_file:
                    registry[prompt_file] = {
                        "version": getattr(attr, "prompt_version", "unknown"),
                        "agent": getattr(attr, "name", "unknown"),
                    }

    # experiment_design.txt is served by HypothesisAgent at runtime.
    if "hypothesis_generation.txt" in registry:
        registry.setdefault("experiment_design.txt", {
            "version": registry["hypothesis_generation.txt"]["version"],
            "agent": "hypothesis_agent",
        })

    for path in sorted(PROMPTS_DIR.glob("*.txt")):
        registry.setdefault(path.name, {"version": "unused", "agent": "unused"})
    return registry