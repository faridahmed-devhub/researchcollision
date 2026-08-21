"""Hypothesis service: persist hypotheses + experiment designs."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import DatasetEntity, Experiment, Hypothesis


class HypothesisService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        workspace_id: str,
        intersection_id: str,
        draft: dict,
    ) -> Hypothesis:
        hyp = Hypothesis(
            workspace_id=workspace_id,
            intersection_id=intersection_id,
            research_question=draft.get("research_question", ""),
            hypothesis_text=draft.get("hypothesis", ""),
            motivation=draft.get("motivation"),
            method=draft.get("method"),
            dataset=draft.get("dataset"),
            baseline=draft.get("baseline"),
            metrics=draft.get("metrics"),
            expected_contribution=draft.get("expected_contribution"),
            risks=draft.get("risks"),
            confidence=0.5,
        )
        self.db.add(hyp)
        self.db.flush()
        return hyp

    def attach_experiment(self, hypothesis: Hypothesis, design: dict) -> Experiment:
        existing = self.db.scalar(
            select(Experiment).where(Experiment.hypothesis_id == hypothesis.id)
        )
        if existing:
            existing.baseline = design.get("baseline")
            existing.proposed_approach = design.get("proposed_approach")
            existing.dataset = design.get("dataset")
            existing.dataset_status = design.get("dataset_status", "INFERRED")
            existing.training_setup = design.get("training_setup")
            existing.evaluation_setup = design.get("evaluation_setup")
            existing.metrics = design.get("metrics")
            existing.ablations = design.get("ablations", [])
            existing.expected_outcomes = design.get("expected_outcomes")
            existing.failure_conditions = design.get("failure_conditions")
            self.db.flush()
            return existing
        exp = Experiment(
            hypothesis_id=hypothesis.id,
            baseline=design.get("baseline"),
            proposed_approach=design.get("proposed_approach"),
            dataset=design.get("dataset"),
            dataset_status=design.get("dataset_status", "INFERRED"),
            training_setup=design.get("training_setup"),
            evaluation_setup=design.get("evaluation_setup"),
            metrics=design.get("metrics"),
            ablations=design.get("ablations", []),
            expected_outcomes=design.get("expected_outcomes"),
            failure_conditions=design.get("failure_conditions"),
        )
        self.db.add(exp)
        self.db.flush()
        return exp

    def known_dataset_names(self) -> list[str]:
        return list(self.db.scalars(select(DatasetEntity.name)))
