from uuid import UUID

from src.application.dtos import StepExecutionOutputDTO
from src.application.dtos.execution_dto import step_execution_to_output_dto
from src.application.errors import NotFoundAppError
from src.domain.ports.repositories import IExecutionRepository, IStepExecutionRepository


class GetExecutionLogs:
    def __init__(
        self,
        execution_repo: IExecutionRepository,
        step_execution_repo: IStepExecutionRepository,
    ) -> None:
        self.execution_repo = execution_repo
        self.step_execution_repo = step_execution_repo

    async def execute(self, execution_id: UUID) -> list[StepExecutionOutputDTO]:
        execution = await self.execution_repo.get_by_id(execution_id)
        if execution is None:
            raise NotFoundAppError("Execution not found")

        steps = await self.step_execution_repo.list_by_execution(execution_id)
        return [step_execution_to_output_dto(s) for s in steps]
