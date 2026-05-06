from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.environment import Environment


class IEnvironmentRepository(ABC):
    @abstractmethod
    async def create(self, environment: Environment) -> Environment: ...

    @abstractmethod
    async def update(self, environment: Environment) -> Environment: ...

    @abstractmethod
    async def get_by_id(self, environment_id: UUID) -> Environment | None: ...

    @abstractmethod
    async def list_by_project(self, project_id: UUID) -> list[Environment]: ...

    @abstractmethod
    async def list_by_project_page(
        self, project_id: UUID, limit: int, offset: int
    ) -> tuple[list[Environment], int]: ...

    @abstractmethod
    async def list_by_pipeline(self, pipeline_id: UUID) -> list[Environment]: ...

    @abstractmethod
    async def get_active_by_project(self, project_id: UUID) -> Environment | None: ...
