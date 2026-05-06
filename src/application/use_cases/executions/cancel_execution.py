from uuid import UUID

from src.application import NotFoundAppError, ValidationAppError
from src.domain.ports.repositories import IExecutionRepository, IStepExecutionRepository
from src.domain.value_objects.execution_status import ExecutionStatus
from src.domain.value_objects.step_execution_status import StepExecutionStatus


class CancelExecution:
    def __init__(
        self,
        execution_repo: IExecutionRepository,
        step_execution_repo: IStepExecutionRepository,
    ) -> None:
        self.execution_repo = execution_repo
        self.step_execution_repo = step_execution_repo

    async def execute(self, execution_id: UUID) -> None:
        execution = await self.execution_repo.get_by_id(execution_id)
        if execution is None:
            raise NotFoundAppError("Execution not found")

        if execution.status not in (
            ExecutionStatus.PENDING,
            ExecutionStatus.RUNNING,
            ExecutionStatus.BLOCKED,
        ):
            raise ValidationAppError(
                "Somente execuções pendentes, em andamento ou bloqueadas podem ser canceladas."
            )

        await self.execution_repo.update(execution.mark_cancelled())

        steps = await self.step_execution_repo.list_by_execution(execution_id)
        msg = "Execução cancelada pelo usuário."
        for se in steps:
            if se.status in (
                StepExecutionStatus.PENDING,
                StepExecutionStatus.RUNNING,
            ):
                await self.step_execution_repo.update(se.mark_skipped(msg))
