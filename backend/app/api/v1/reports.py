"""Report endpoints: generate + fetch research reports."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_owned_workspace
from app.core.exceptions import NotFoundError
from app.db.database import get_db
from app.db.models import GeneratedReport, Workspace
from app.schemas.misc import ReportCreate, ReportOut
from app.services.report_service import ReportService

router = APIRouter(tags=["reports"])


@router.post("/reports", response_model=ReportOut, status_code=201)
def create_report(
    payload: ReportCreate,
    ws: Workspace = Depends(get_owned_workspace),
    db: Session = Depends(get_db),
) -> GeneratedReport:
    service = ReportService(db)
    report = service.generate(
        workspace_id=ws.id,
        workspace_name=ws.name,
        fmt=payload.format,
        job_id=payload.job_id,
        title=payload.title,
    )
    db.commit()
    return report


@router.get("/workspaces/{workspace_id}/reports", response_model=list[ReportOut])
def list_reports(
    ws: Workspace = Depends(get_owned_workspace),
    db: Session = Depends(get_db),
) -> list[GeneratedReport]:
    return list(
        db.scalars(
            select(GeneratedReport)
            .where(GeneratedReport.workspace_id == ws.id)
            .order_by(GeneratedReport.created_at.desc())
        )
    )


@router.get("/reports/{report_id}", response_model=ReportOut)
def get_report(
    report_id: str,
    ws: Workspace = Depends(get_owned_workspace),
    db: Session = Depends(get_db),
) -> GeneratedReport:
    report = db.get(GeneratedReport, report_id)
    if report is None or report.workspace_id != ws.id:
        raise NotFoundError("Report not found")
    return report
