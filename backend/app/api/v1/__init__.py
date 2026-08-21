"""API v1 router aggregation."""
from fastapi import APIRouter

from app.api.v1 import (
    auth,
    collaborations,
    discovery,
    evidence,
    gaps,
    hypotheses,
    intersections,
    meta,
    papers,
    reports,
    research_profiles,
    researchers,
    workspaces,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(workspaces.router)
api_router.include_router(research_profiles.router)
api_router.include_router(researchers.router)
api_router.include_router(papers.router)
api_router.include_router(discovery.router)
api_router.include_router(intersections.router)
api_router.include_router(gaps.router)
api_router.include_router(hypotheses.router)
api_router.include_router(collaborations.router)
api_router.include_router(evidence.router)
api_router.include_router(reports.router)
api_router.include_router(meta.router)
