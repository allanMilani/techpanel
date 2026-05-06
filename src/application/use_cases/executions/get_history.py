from uuid import UUID

from src.application.dtos import ExecutionOutputDTO
from src.application.dtos.execution_dto import execution_to_output_dto
from src.application.dtos.pagination_dto import PaginatedResult, offset_for_page
from src.domain.ports.repositories import IExecutionRepository


class GetHistory:
    def __init__(self, execution_repo: IExecutionRepository) -> None:
        self.execution_repo = execution_repo

    async def execute(
        self, pipeline_id: UUID, page: int, per_page: int
    ) -> PaginatedResult[ExecutionOutputDTO]:
        offset = offset_for_page(page, per_page)
        executions, total = await self.execution_repo.list_by_pipeline_page(
            pipeline_id, per_page, offset
        )
        items = [execution_to_output_dto(e) for e in executions]
        return PaginatedResult(
            items=items, total=total, page=page, per_page=per_page
        )
