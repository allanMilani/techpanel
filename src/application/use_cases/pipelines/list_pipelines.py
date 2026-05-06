from uuid import UUID

from src.application.dtos import PipelineSummaryDTO
from src.application.dtos.pagination_dto import PaginatedResult, offset_for_page
from src.application.dtos.pipeline_dto import pipeline_to_summary_dto
from src.domain.ports.repositories import IPipelineRepository


class ListPipelines:
    def __init__(
        self,
        pipeline_repo: IPipelineRepository,
    ) -> None:
        self.pipeline_repo = pipeline_repo

    async def execute(
        self, environment_id: UUID, page: int, per_page: int
    ) -> PaginatedResult[PipelineSummaryDTO]:
        offset = offset_for_page(page, per_page)
        pipelines, total = await self.pipeline_repo.list_by_environment_page(
            environment_id, per_page, offset
        )
        items = [pipeline_to_summary_dto(pipeline) for pipeline in pipelines]
        return PaginatedResult(
            items=items, total=total, page=page, per_page=per_page
        )
