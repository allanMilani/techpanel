from uuid import UUID
from src.application import NotFoundAppError
from src.application.dtos import PipelineOutputDTO
from src.application.dtos.pipeline_dto import pipeline_step_to_output_dto
from src.domain.ports.repositories import IPipelineRepository


class GetPipeline:
    def __init__(
        self,
        pipeline_repo: IPipelineRepository,
    ) -> None:
        self.pipeline_repo = pipeline_repo

    async def execute(self, pipeline_id: UUID) -> list[PipelineOutputDTO]:
        pipeline = await self.pipeline_repo.get_by_id(pipeline_id)
        if pipeline is None:
            raise NotFoundAppError("Pipeline not found")

        steps = await self.pipeline_repo.list_steps(pipeline_id)
        return [pipeline_step_to_output_dto(step) for step in steps]
