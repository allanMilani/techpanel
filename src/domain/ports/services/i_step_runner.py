from abc import ABC, abstractmethod

from src.domain.entities.pipeline_step import PipelineStep


class IStepRunner(ABC):
    @abstractmethod
    async def run(self, step: PipelineStep) -> tuple[int, str]: ...
