from uuid import UUID


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


class ActiveExecutionConflictError(ConflictAppError):
    """Já existe execução ativa no projeto; o cliente pode cancelar `blocking_execution_id`."""

    def __init__(self, blocking_execution_id: UUID) -> None:
        self.blocking_execution_id = blocking_execution_id
        super().__init__(
            "Já existe execução ativa para este projeto. Cancele a execução em andamento ou aguarde a conclusão."
        )
