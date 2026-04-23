from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.pipeline import Pipeline
from src.domain.entities.pipeline_step import PipelineStep


class IPipelineRepository(ABC):
    @abstractmethod
    async def create(self, pipeline: Pipeline) -> Pipeline: ...

    @abstractmethod
    async def update(self, pipeline: Pipeline) -> Pipeline: ...

    @abstractmethod
    async def get_by_id(self, pipeline_id: UUID) -> Pipeline | None: ...

    @abstractmethod
    async def list_by_environment(self, environment_id: UUID) -> list[Pipeline]: ...

    @abstractmethod
    async def delete(self, pipeline_id: UUID) -> None: ...

    @abstractmethod
    async def add_step(self, step: PipelineStep) -> PipelineStep: ...

    @abstractmethod
    async def update_step(self, step: PipelineStep) -> PipelineStep: ...

    @abstractmethod
    async def remove_step(self, step_id: UUID) -> None: ...

    @abstractmethod
    async def list_steps(self, pipeline_id: UUID) -> list[PipelineStep]: ...

    @abstractmethod
    async def get_next_step(
        self, pipeline_id: UUID, after_order: int
    ) -> PipelineStep | None: ...
