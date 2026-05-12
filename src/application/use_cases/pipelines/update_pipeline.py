from uuid import UUID
from src.application import NotFoundAppError
from src.application.dtos import PipelineSummaryDTO, UpdatePipelineInputDTO
from src.application.dtos.pipeline_dto import pipeline_to_summary_dto
from src.domain.entities.pipeline import Pipeline
from src.domain.ports.repositories import IPipelineRepository


class UpdatePipeline:
    def __init__(
        self,
        pipeline_repo: IPipelineRepository,
    ) -> None:
        self.pipeline_repo = pipeline_repo

    async def execute(
        self, pipeline_id: UUID, dto: UpdatePipelineInputDTO
    ) -> PipelineSummaryDTO:
        pipeline = await self.pipeline_repo.get_by_id(pipeline_id)
        if pipeline is None:
            raise NotFoundAppError("Pipeline not found")

        updated = Pipeline(
            id=pipeline.id,
            environment_id=pipeline.environment_id,
            name=dto.name.strip(),
            description=dto.description,
            run_git_workspace_sync=dto.run_git_workspace_sync,
            steps=pipeline.steps,
        )

        persisted = await self.pipeline_repo.update(updated)
        return pipeline_to_summary_dto(persisted)
