"""Research Intersection Agent — the core product agent."""
from __future__ import annotations

from app.agents.base import BaseAgent
from app.core.constants import DiscoveryMode
from app.providers.llm.base import IntersectionResult


class IntersectionAgent(BaseAgent):
    name = "intersection_agent"
    prompt_file = "intersection_discovery.txt"
    prompt_version = "v1"
    task_name = "intersection_discovery"
    output_schema_name = "IntersectionResult"
    output_model = IntersectionResult

    async def discover(
        self,
        *,
        researcher_a: dict,
        researcher_b: dict,
        gaps: list[dict],
        mode: DiscoveryMode = DiscoveryMode.NORMAL,
        max_intersections: int = 5,
    ) -> IntersectionResult:
        input_data = {
            "mode": mode.value if isinstance(mode, DiscoveryMode) else str(mode),
            "researcher_a": self._compact(researcher_a),
            "researcher_b": self._compact(researcher_b),
            "gaps": [
                {
                    "description": g.get("description", ""),
                    "gap_type": g.get("gap_type", ""),
                    "confidence": g.get("confidence", 0.5),
                    "evidence_ids": g.get("evidence_ids", []),
                }
                for g in gaps[:12]
            ],
            "max_intersections": max_intersections,
        }
        return await self.run_structured(input_data)  # type: ignore[return-value]

    @staticmethod
    def _compact(researcher: dict) -> dict:
        traj = researcher.get("trajectory") or {}
        return {
            "name": researcher.get("name", ""),
            "affiliation": researcher.get("affiliation"),
            "topics": researcher.get("topics", [])[:8],
            "methods": researcher.get("methods", [])[:8],
            "domains": researcher.get("domains", [])[:5],
            "trajectory": {
                "historical_focus": traj.get("historical_focus", []),
                "current_focus": traj.get("current_focus", []),
                "emerging_interests": traj.get("emerging_interests", []),
                "methodology_shifts": traj.get("methodology_shifts", []),
                "domain_shifts": traj.get("domain_shifts", []),
                "summary": (traj.get("summary") or "")[:500],
                "evidence_ids": traj.get("evidence_ids", [])[:10],
                "methods_pool": researcher.get("methods_pool", [])[:8],
                "domains": researcher.get("domains", [])[:5],
            },
        }
