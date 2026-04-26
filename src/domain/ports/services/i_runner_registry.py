from abc import ABC, abstractmethod

from src.domain.ports.services.i_step_runner import IStepRunner
from src.domain.value_objects.step_type import StepType


class IRunnerRegistry(ABC):
    @abstractmethod
    def get(self, step_type: StepType) -> IStepRunner: ...
