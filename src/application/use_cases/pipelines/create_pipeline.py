from src.application.dtos import CreatePipelineInputDTO, PipelineSummaryDTO
from src.application.dtos.pipeline_dto import pipeline_to_summary_dto
from src.domain.entities.pipeline import Pipeline
from src.domain.ports.repositories import IPipelineRepository


class CreatePipeline:
    def __init__(self, pipeline_repo: IPipelineRepository) -> None:
        self.pipeline_repo = pipeline_repo

    async def execute(self, dto: CreatePipelineInputDTO) -> PipelineSummaryDTO:
        pipeline = Pipeline.create(
            name=dto.name,
            environment_id=str(dto.environment_id),
            description=dto.description,
        )
        created = await self.pipeline_repo.create(pipeline)
        return pipeline_to_summary_dto(created)
