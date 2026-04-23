class ApplicationError(Exception):
    """Base error for the application layer."""


class ValidationAppError(ApplicationError):
    """Validation error for the application layer."""


class NotFoundAppError(ApplicationError):
    """Resource not found."""


class UnauthorizedAppError(ApplicationError):
    """Unauthorized / invalid credential."""


class ForbiddenAppError(ApplicationError):
    """Forbidden operation."""


class ConflictAppError(ApplicationError):
    """Business rule conflict (e.g. execution lock)."""
