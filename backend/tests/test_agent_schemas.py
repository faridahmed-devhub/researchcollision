"""Regression tests: AGENT_SCHEMAS completeness + discovery-mode vocabulary."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.providers.llm.base import AGENT_SCHEMAS
from app.schemas.profile import ResearchDNA


def test_agent_schemas_contains_research_dna():
    assert "ResearchDNA" in AGENT_SCHEMAS
    assert AGENT_SCHEMAS["ResearchDNA"] == ResearchDNA.model_json_schema()


def test_profile_agent_schema_is_registered():
    """The real crash: ProfileAgent.output_schema_name -> AGENT_SCHEMAS KeyError."""
    from app.agents.profile_agent import ProfileAgent

    assert ProfileAgent.output_schema_name == "ResearchDNA"
    assert ProfileAgent.output_schema_name in AGENT_SCHEMAS


def test_every_agent_schema_is_registered():
    from app.agents.gap_agent import GapAgent
    from app.agents.hypothesis_agent import HypothesisAgent
    from app.agents.intersection_agent import IntersectionAgent
    from app.agents.paper_analysis_agent import PaperAnalysisAgent
    from app.agents.profile_agent import ProfileAgent
    from app.agents.trajectory_agent import TrajectoryAgent

    for agent_cls in [
        PaperAnalysisAgent,
        TrajectoryAgent,
        GapAgent,
        IntersectionAgent,
        HypothesisAgent,
        ProfileAgent,
    ]:
        assert agent_cls.output_schema_name in AGENT_SCHEMAS, agent_cls.__name__


def test_discovery_mode_accepts_backend_vocabulary():
    from app.core.constants import DiscoveryMode
    from app.schemas.discovery import DiscoveryJobCreate

    payload = DiscoveryJobCreate(
        workspace_id="w", researcher_a_id="r", mode="serendipity"
    )
    assert payload.mode == DiscoveryMode.SERENDIPITY


def test_discovery_mode_rejects_frontend_legacy_values():
    from app.schemas.discovery import DiscoveryJobCreate

    for bad in ("exploratory", "targeted"):
        with pytest.raises(ValidationError):
            DiscoveryJobCreate(
                workspace_id="w", researcher_a_id="r", mode=bad
            )