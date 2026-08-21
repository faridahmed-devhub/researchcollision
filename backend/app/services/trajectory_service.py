"""Trajectory service: compute + persist researcher trajectories."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    DatasetEntity,
    Method,
    Paper,
    PaperDataset,
    PaperMethod,
    PaperTopic,
    ResearchTrajectory,
    Researcher,
    Topic,
)


class TrajectoryService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def papers_for_researcher(self, researcher: Researcher) -> list[Paper]:
        from app.db.repositories.paper_repository import PaperRepository

        return PaperRepository(self.db).for_researcher(researcher.id)

    def _linked_names(self, kind: str, paper_id: str) -> list[str]:
        if kind == "topics":
            rows = (
                self.db.query(Topic.name)
                .join(PaperTopic, PaperTopic.topic_id == Topic.id)
                .filter(PaperTopic.paper_id == paper_id)
                .all()
            )
        elif kind == "methods":
            rows = (
                self.db.query(Method.name)
                .join(PaperMethod, PaperMethod.method_id == Method.id)
                .filter(PaperMethod.paper_id == paper_id)
                .all()
            )
        else:
            rows = (
                self.db.query(DatasetEntity.name)
                .join(PaperDataset, PaperDataset.dataset_id == DatasetEntity.id)
                .filter(PaperDataset.paper_id == paper_id)
                .all()
            )
        return [r[0] for r in rows]

    def paper_context(self, papers: list[Paper]) -> list[dict]:
        """Compact per-paper context with topics/methods for the agent."""
        return [
            {
                "title": p.title,
                "year": p.publication_year,
                "topics": self._linked_names("topics", p.id),
                "methods": self._linked_names("methods", p.id),
            }
            for p in papers
        ]

    def save_trajectory(
        self,
        *,
        workspace_id: str,
        researcher_id: str,
        analysis_dict: dict,
        summary: str,
    ) -> ResearchTrajectory:
        existing = self.db.scalar(
            select(ResearchTrajectory).where(
                ResearchTrajectory.workspace_id == workspace_id,
                ResearchTrajectory.researcher_id == researcher_id,
            )
        )
        if existing:
            existing.trajectory_json = analysis_dict
            existing.summary = summary
            self.db.flush()
            return existing
        traj = ResearchTrajectory(
            workspace_id=workspace_id,
            researcher_id=researcher_id,
            trajectory_json=analysis_dict,
            summary=summary,
        )
        self.db.add(traj)
        self.db.flush()
        return traj

    def get(self, workspace_id: str, researcher_id: str) -> ResearchTrajectory | None:
        return self.db.scalar(
            select(ResearchTrajectory).where(
                ResearchTrajectory.workspace_id == workspace_id,
                ResearchTrajectory.researcher_id == researcher_id,
            )
        )
