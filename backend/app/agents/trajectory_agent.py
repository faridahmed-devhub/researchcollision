"""Trajectory Agent — chronological researcher trajectory analysis."""
from __future__ import annotations

from app.agents.base import BaseAgent
from app.providers.llm.base import TrajectoryAnalysis


class TrajectoryAgent(BaseAgent):
    name = "trajectory_agent"
    prompt_file = "trajectory_analysis.txt"
    prompt_version = "v1"
    task_name = "trajectory_analysis"
    output_schema_name = "TrajectoryAnalysis"
    output_model = TrajectoryAnalysis

    async def analyze(
        self, *, researcher_name: str, papers: list[dict], evidence_ids: list[str] | None = None
    ) -> TrajectoryAnalysis:
        input_data = {
            "researcher_name": researcher_name,
            "papers": [
                {
                    "title": p.get("title", ""),
                    "year": p.get("year"),
                    "topics": p.get("topics", [])[:6],
                    "methods": p.get("methods", [])[:6],
                }
                for p in papers[:40]
            ],
            "evidence_ids": evidence_ids or [],
        }
        return await self.run_structured(input_data)  # type: ignore[return-value]
