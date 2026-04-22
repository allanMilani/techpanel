from uuid import UUID

from src.application.dtos import ExecutionOutputDTO
from src.application.dtos.execution_dto import execution_to_output_dto
from src.domain.ports.repositories import IExecutionRepository


class GetHistory:
    def __init__(self, execution_repo: IExecutionRepository) -> None:
        self.execution_repo = execution_repo

    async def execute(self, pipeline_id: UUID) -> list[ExecutionOutputDTO]:
        executions = await self.execution_repo.list_by_pipeline(pipeline_id)
        return [execution_to_output_dto(e) for e in executions]
