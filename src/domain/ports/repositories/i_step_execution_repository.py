from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.step_execution import StepExecution


class IStepExecutionRepository(ABC):
    @abstractmethod
    async def create_many(self, steps: list[StepExecution]) -> list[StepExecution]: ...

    @abstractmethod
    async def update(self, step_execution: StepExecution) -> StepExecution: ...

    @abstractmethod
    async def get_by_id(self, step_execution_id: UUID) -> StepExecution | None: ...

    @abstractmethod
    async def get_last_by_execution(
        self, execution_id: UUID
    ) -> StepExecution | None: ...

    @abstractmethod
    async def list_by_execution(self, execution_id: UUID) -> list[StepExecution]: ...

    @abstractmethod
    async def skip_remaining(self, execution_id: UUID, after_order: int) -> None: ...
