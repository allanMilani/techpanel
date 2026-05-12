from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.pipeline_step import PipelineStep


class IStepRunner(ABC):
    @abstractmethod
    async def run(
        self, step: PipelineStep, *, execution_id: UUID | None = None
    ) -> tuple[int, str]: ...
