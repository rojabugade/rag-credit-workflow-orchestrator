from typing import Any


class CreditFlowError(Exception):
    code = "internal_error"
    status_code = 500

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class NotFoundError(CreditFlowError):
    code = "not_found"
    status_code = 404


class ConflictError(CreditFlowError):
    code = "conflict"
    status_code = 409


class AuthorizationError(CreditFlowError):
    code = "forbidden"
    status_code = 403


class ProviderError(CreditFlowError):
    code = "provider_error"
    status_code = 502


class EvidenceValidationError(CreditFlowError):
    code = "invalid_evidence"
    status_code = 422
