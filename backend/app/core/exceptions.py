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


class ProviderThrottledError(ProviderError):
    """The provider returned a throttling response (HTTP 429) that may carry a
    server-provided ``retry_after`` (seconds). Never treat as an empty result or
    as an exclusion — only as a temporary unavailability signal.
    """

    code = "provider_throttled"
    status_code = 429

    def __init__(self, message: str = "Provider throttled", *, retry_after: int | None = None, provider: str = "provider") -> None:
        super().__init__(message, code="provider_throttled")
        self.retry_after = retry_after
        self.provider = provider


class RateLimitAppError(AppError):
    status_code = 429
    code = "rate_limited"


class JobControlError(AppError):
    status_code = 409
    code = "job_control_error"


class NotImplementedAppError(AppError):
    status_code = 501
    code = "not_implemented"
