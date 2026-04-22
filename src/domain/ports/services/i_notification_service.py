from abc import ABC, abstractmethod

from src.domain.entities.execution import Execution
from src.domain.entities.step_execution import StepExecution


class INotificationService(ABC):
    @abstractmethod
    async def notify_execution_failed(
        self,
        execution: Execution,
        failed_step: StepExecution | None,
    ) -> None:
        ...