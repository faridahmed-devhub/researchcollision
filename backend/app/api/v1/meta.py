"""Meta endpoints: provider status (mock-mode banner) + settings."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_owned_workspace
from app.core.config import settings
from app.db.database import get_db
from app.db.models import User, Workspace
from app.schemas.misc import ProviderStatus
from app.services.settings_service import SettingsService

router = APIRouter(tags=["meta"])


@router.get("/meta/provider-status", response_model=ProviderStatus)
def provider_status(user: User = Depends(get_current_user)) -> ProviderStatus:
    return ProviderStatus(
        llm_provider=("mock" if settings.is_mock_llm else settings.llm_provider),
        llm_model=settings.llm_model or ("mock-deterministic-v1" if settings.is_mock_llm else ""),
        mock_mode=settings.mock_mode,
        embedding_provider=settings.embedding_provider,
        literature_provider=settings.literature_provider,
        app_env=settings.app_env,
    )


@router.get("/workspaces/{workspace_id}/settings")
def get_workspace_settings(
    ws: Workspace = Depends(get_owned_workspace),
    db: Session = Depends(get_db),
) -> dict:
    service = SettingsService(db)
    return {
        "collaboration_weights": service.collaboration_weights(),
        "discovery_mode": ws.discovery_mode,
    }


@router.put("/workspaces/{workspace_id}/settings")
def update_workspace_settings(
    payload: dict,
    ws: Workspace = Depends(get_owned_workspace),
    db: Session = Depends(get_db),
) -> dict:
    service = SettingsService(db)
    if "collaboration_weights" in payload and isinstance(payload["collaboration_weights"], dict):
        service.set("collaboration_weights", payload["collaboration_weights"])
    db.commit()
    return {
        "collaboration_weights": service.collaboration_weights(),
        "discovery_mode": ws.discovery_mode,
    }
