"""Application exception hierarchy mapped to HTTP responses."""
from __future__ import annotations


class AppError(Exception):
    """Base error with an HTTP status code and machine-readable code."""

    status_code = 500
    code = "internal_error"

    def __init__(self, message: str = "Internal error", *, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        if code:
            self.code = code


class AuthenticationError(AppError):
    status_code = 401
    code = "authentication_failed"


class AuthorizationError(AppError):
    status_code = 403
    code = "forbidden"


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class ConflictError(AppError):
    status_code = 409
    code = "conflict"


class ValidationAppError(AppError):
    status_code = 422
    code = "validation_error"


class UploadValidationError(ValidationAppError):
    status_code = 415
    code = "upload_validation_error"


class ProviderError(AppError):
    """An external provider (LLM / literature / embeddings) failed."""

    status_code = 502
    code = "provider_error"


class RateLimitAppError(AppError):
    status_code = 429
    code = "rate_limited"


class JobControlError(AppError):
    status_code = 409
    code = "job_control_error"
