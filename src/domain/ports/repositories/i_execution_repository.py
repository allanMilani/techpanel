from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.execution import Execution


class IExecutionRepository(ABC):
    @abstractmethod
    async def create(self, execution: Execution) -> Execution: ...

    @abstractmethod
    async def update(self, execution: Execution) -> Execution: ...

    @abstractmethod
    async def get_by_id(self, execution_id: UUID) -> Execution | None: ...

    @abstractmethod
    async def list_by_pipeline(self, pipeline_id: UUID) -> list[Execution]: ...

    @abstractmethod
    async def get_active_execution_for_environment(
        self, environment_id: UUID
    ) -> Execution | None: ...

    @abstractmethod
    async def get_active_execution_for_project(
        self, project_id: UUID
    ) -> Execution | None: ...
