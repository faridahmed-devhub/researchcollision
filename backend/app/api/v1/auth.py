"""Auth endpoints: register + login."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import create_access_token, hash_password, verify_password
from app.db.database import get_db
from app.db.models import AuditLog, User
from app.db.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    repo = UserRepository(db)
    if repo.get_by_email(str(payload.email)) is not None:
        raise ConflictError("An account with this email already exists")
    user = repo.create(email=str(payload.email), password_hash=hash_password(payload.password), name=payload.name)
    db.add(AuditLog(user_id=user.id, action="auth.register"))
    db.commit()
    return TokenResponse(
        access_token=create_access_token(user.id),
        user=UserOut.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    repo = UserRepository(db)
    user = repo.get_by_email(str(payload.email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise AuthenticationError("Invalid email or password")
    db.add(AuditLog(user_id=user.id, action="auth.login"))
    db.commit()
    return TokenResponse(
        access_token=create_access_token(user.id),
        user=UserOut.model_validate(user),
    )
