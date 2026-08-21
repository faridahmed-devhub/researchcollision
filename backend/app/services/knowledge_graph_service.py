"""Knowledge graph service — relational graph queries (nodes + edges JSON)."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    DatasetEntity,
    Method,
    Paper,
    PaperAuthor,
    PaperDataset,
    PaperMethod,
    PaperTopic,
    ResearchGap,
    Researcher,
    Topic,
)


class KnowledgeGraphService:
    """Builds a lightweight nodes/edges graph from relational tables.

    Relationships:
      Researcher -authored-> Paper
      Paper -studies-> Topic
      Paper -uses-> Method
      Paper -uses-> Dataset
      Paper -identifies-> Gap (via workspace gaps linked to evidence)
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def build_graph(self, workspace_id: str, limit: int = 300) -> dict:
        nodes: dict[str, dict] = {}
        edges: list[dict] = []

        papers = list(
            self.db.scalars(
                select(Paper).join(PaperAuthor, PaperAuthor.paper_id == Paper.id)
                .where(PaperAuthor.researcher_id.isnot(None))
                .limit(limit)
            )
        )
        paper_ids = [p.id for p in papers]
        if not paper_ids:
            return {"nodes": [], "edges": []}

        authorships = list(
            self.db.scalars(
                select(PaperAuthor).where(
                    PaperAuthor.paper_id.in_(paper_ids),
                    PaperAuthor.researcher_id.isnot(None),
                )
            )
        )
        researcher_ids = {a.researcher_id for a in authorships}
        researchers = {
            r.id: r
            for r in self.db.scalars(
                select(Researcher).where(Researcher.id.in_(researcher_ids))
            )
        }

        for rid, r in researchers.items():
            nodes[f"researcher:{rid}"] = {
                "id": f"researcher:{rid}",
                "label": r.name,
                "type": "researcher",
            }
        for p in papers:
            nodes[f"paper:{p.id}"] = {
                "id": f"paper:{p.id}",
                "label": p.title[:80],
                "type": "paper",
                "year": p.publication_year,
            }
        for a in authorships:
            edges.append({
                "source": f"researcher:{a.researcher_id}",
                "target": f"paper:{a.paper_id}",
                "relation": "authored",
            })

        topic_links = list(
            self.db.scalars(select(PaperTopic).where(PaperTopic.paper_id.in_(paper_ids)))
        )
        topics = {
            t.id: t
            for t in self.db.scalars(select(Topic).where(Topic.id.in_({l.topic_id for l in topic_links})))
        } if topic_links else {}
        for l in topic_links:
            t = topics.get(l.topic_id)
            if not t:
                continue
            nodes[f"topic:{t.id}"] = {"id": f"topic:{t.id}", "label": t.name, "type": "topic"}
            edges.append({"source": f"paper:{l.paper_id}", "target": f"topic:{t.id}", "relation": "studies"})

        method_links = list(
            self.db.scalars(select(PaperMethod).where(PaperMethod.paper_id.in_(paper_ids)))
        )
        methods = {
            m.id: m
            for m in self.db.scalars(select(Method).where(Method.id.in_({l.method_id for l in method_links})))
        } if method_links else {}
        for l in method_links:
            m = methods.get(l.method_id)
            if not m:
                continue
            nodes[f"method:{m.id}"] = {"id": f"method:{m.id}", "label": m.name, "type": "method"}
            edges.append({"source": f"paper:{l.paper_id}", "target": f"method:{m.id}", "relation": "uses"})

        dataset_links = list(
            self.db.scalars(select(PaperDataset).where(PaperDataset.paper_id.in_(paper_ids)))
        )
        datasets = {
            d.id: d
            for d in self.db.scalars(
                select(DatasetEntity).where(DatasetEntity.id.in_({l.dataset_id for l in dataset_links}))
            )
        } if dataset_links else {}
        for l in dataset_links:
            d = datasets.get(l.dataset_id)
            if not d:
                continue
            nodes[f"dataset:{d.id}"] = {"id": f"dataset:{d.id}", "label": d.name, "type": "dataset"}
            edges.append({"source": f"paper:{l.paper_id}", "target": f"dataset:{d.id}", "relation": "uses"})

        gaps = list(self.db.scalars(select(ResearchGap).where(ResearchGap.workspace_id == workspace_id).limit(50)))
        for g in gaps:
            nodes[f"gap:{g.id}"] = {
                "id": f"gap:{g.id}",
                "label": g.description[:80],
                "type": "gap",
            }
            edges.append({
                "source": f"workspace:{workspace_id}",
                "target": f"gap:{g.id}",
                "relation": "identifies",
            })
        nodes[f"workspace:{workspace_id}"] = {
            "id": f"workspace:{workspace_id}",
            "label": "Workspace",
            "type": "workspace",
        }

        return {"nodes": list(nodes.values()), "edges": edges}
