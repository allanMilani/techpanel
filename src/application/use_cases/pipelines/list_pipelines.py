from uuid import UUID

from src.application.dtos import PipelineSummaryDTO
from src.application.dtos.pipeline_dto import pipeline_to_summary_dto
from src.domain.ports.repositories import IPipelineRepository


class ListPipelines:
    def __init__(
        self,
        pipeline_repo: IPipelineRepository,
    ) -> None:
        self.pipeline_repo = pipeline_repo

    async def execute(self, environment_id: UUID) -> list[PipelineSummaryDTO]:
        pipelines = await self.pipeline_repo.list_by_environment(environment_id)
        return [pipeline_to_summary_dto(pipeline) for pipeline in pipelines]
