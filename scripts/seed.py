"""Seed the database with demo data.

Usage:
    cd backend && python ../scripts/seed.py [--with-job]

Creates:
- demo user  (demo@researchcollision.dev / demo1234)
- demo workspace
- SYNTHETIC DEMO researchers + papers (clearly marked fictional)
- optionally runs one discovery job end-to-end
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from sqlalchemy import select  # noqa: E402

from app.core.logging import configure_logging  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.database import SessionLocal, engine, init_db  # noqa: E402
from app.db.models import Paper, PaperAuthor, Researcher, ResearcherAlias, User, Workspace  # noqa: E402
from app.db.repositories.job_repository import JobRepository  # noqa: E402
from app.core.constants import DISCOVERY_STEPS  # noqa: E402
from app.providers.literature.mock import MockLiteratureProvider  # noqa: E402
from app.services.paper_service import PaperService  # noqa: E402
from app.utils.synthetic_data import SYNTHETIC_PAPERS  # noqa: E402

DEMO_EMAIL = "demo@researchcollision.dev"
DEMO_PASSWORD = "demo1234"

SEED_RESEARCHERS = [
    {"name": "Dr. Amara Chen", "affiliation": "Institute of Applied Language Technology",
     "bio": "Works on low-resource NLP, multilingual models, and data-efficient learning.",
     "aliases": ["A. Chen"]},
    {"name": "Prof. Diego Alvarez", "affiliation": "Center for Climate Systems Modeling",
     "bio": "Climate model downscaling, extreme weather prediction, uncertainty quantification.",
     "aliases": ["D. Alvarez"]},
    {"name": "Dr. Priya Raghavan", "affiliation": "Medical Imaging Research Lab",
     "bio": "Deep learning for medical image segmentation and clinical deployment.",
     "aliases": ["P. Raghavan"]},
    {"name": "Dr. Jonas Weber", "affiliation": "Graph Learning Group",
     "bio": "Graph neural networks, knowledge graphs, relational reasoning.",
     "aliases": ["J. Weber"]},
    {"name": "Prof. Elena Petrova", "affiliation": "Speech and Audio Systems Group",
     "bio": "Speech recognition for under-resourced languages and speech accessibility.",
     "aliases": ["E. Petrova"]},
]


def seed(with_job: bool = False) -> None:
    configure_logging("INFO")
    init_db(engine, Base.metadata)
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == DEMO_EMAIL))
        if user is None:
            user = User(
                email=DEMO_EMAIL,
                password_hash=hash_password(DEMO_PASSWORD),
                name="Demo Researcher",
            )
            db.add(user)
            db.flush()
            print(f"[seed] created demo user: {DEMO_EMAIL} / {DEMO_PASSWORD}")
        else:
            print("[seed] demo user already exists")

        ws = db.scalar(
            select(Workspace).where(Workspace.user_id == user.id, Workspace.name == "Demo Workspace")
        )
        if ws is None:
            ws = Workspace(user_id=user.id, name="Demo Workspace", description="Seeded demo workspace")
            db.add(ws)
            db.flush()
            print("[seed] created demo workspace")

        researcher_by_name: dict[str, Researcher] = {}
        for rd in SEED_RESEARCHERS:
            existing = db.scalar(select(Researcher).where(Researcher.name == rd["name"]))
            if existing:
                researcher_by_name[rd["name"]] = existing
                continue
            r = Researcher(name=rd["name"], affiliation=rd["affiliation"], bio=rd["bio"], is_synthetic=True)
            db.add(r)
            db.flush()
            for alias in rd["aliases"]:
                db.add(ResearcherAlias(researcher_id=r.id, alias=alias))
            researcher_by_name[rd["name"]] = r
        print(f"[seed] synthetic researchers ready: {len(researcher_by_name)}")

        paper_service = PaperService(db)
        mock_lit = MockLiteratureProvider()
        added = 0
        for p in SYNTHETIC_PAPERS:
            meta = mock_lit._to_metadata(p)  # noqa: SLF001 - same package
            paper, created = paper_service.upsert_from_metadata(meta)
            if created:
                added += 1
            # synthetic topics double as method tags for the demo graph
            paper_service.link_methods(paper.id, p["topics"])
            for author_name in p["authors"]:
                r = researcher_by_name.get(author_name.strip())
                if r is None:
                    continue
                exists = (
                    db.query(PaperAuthor)
                    .filter(PaperAuthor.paper_id == paper.id, PaperAuthor.researcher_id == r.id)
                    .first()
                )
                if not exists:
                    db.add(PaperAuthor(paper_id=paper.id, researcher_id=r.id, author_name=author_name))
        db.commit()
        total = len(list(db.scalars(select(Paper))))
        print(f"[seed] papers added now: {added}; total papers in DB: {total}")

        if with_job:
            print("[seed] running discovery job (Dr. Amara Chen x Prof. Elena Petrova)...")
            from app.workers.job_runner import JobRunner

            ra = researcher_by_name["Dr. Amara Chen"]
            rb = researcher_by_name["Prof. Elena Petrova"]
            job = JobRepository(db).create_job(
                workspace_id=ws.id,
                user_id=user.id,
                job_type="discovery",
                config={
                    "workspace_id": ws.id,
                    "researcher_a_id": ra.id,
                    "researcher_b_id": rb.id,
                    "mode": "normal",
                    "max_papers": 8,
                    "generate_hypotheses": True,
                },
                total_steps=len(DISCOVERY_STEPS),
            )
            db.commit()
            status = asyncio.run(JobRunner(db).execute(job))
            print(f"[seed] discovery job finished with status: {status}")

        print("[seed] done.")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--with-job", action="store_true", help="Also run a full discovery job")
    args = parser.parse_args()
    seed(with_job=args.with_job)
