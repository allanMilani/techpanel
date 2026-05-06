from uuid import UUID

from src.application import NotFoundAppError
from src.application.dtos import PipelineOutputDTO
from src.application.dtos.pagination_dto import PaginatedResult, offset_for_page
from src.application.dtos.pipeline_dto import pipeline_step_to_output_dto
from src.domain.ports.repositories import IPipelineRepository


class GetPipeline:
    def __init__(
        self,
        pipeline_repo: IPipelineRepository,
    ) -> None:
        self.pipeline_repo = pipeline_repo

    async def execute(
        self, pipeline_id: UUID, page: int, per_page: int
    ) -> PaginatedResult[PipelineOutputDTO]:
        pipeline = await self.pipeline_repo.get_by_id(pipeline_id)
        if pipeline is None:
            raise NotFoundAppError("Pipeline not found")

        offset = offset_for_page(page, per_page)
        steps, total = await self.pipeline_repo.list_steps_page(
            pipeline_id, per_page, offset
        )
        items = [pipeline_step_to_output_dto(step) for step in steps]
        return PaginatedResult(
            items=items, total=total, page=page, per_page=per_page
        )

    async def execute_all_steps(self, pipeline_id: UUID) -> list[PipelineOutputDTO]:
        """Lista completa de passos (ex.: painel de execução); a API pública usa `execute` paginado."""
        pipeline = await self.pipeline_repo.get_by_id(pipeline_id)
        if pipeline is None:
            raise NotFoundAppError("Pipeline not found")

        steps = await self.pipeline_repo.list_steps(pipeline_id)
        return [pipeline_step_to_output_dto(step) for step in steps]
