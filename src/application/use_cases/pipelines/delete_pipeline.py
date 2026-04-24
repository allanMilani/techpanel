from uuid import UUID
from src.application import NotFoundAppError
from src.domain.ports.repositories import IPipelineRepository


class DeletePipeline:
    def __init__(
        self,
        pipeline_repo: IPipelineRepository,
    ) -> None:
        self.pipeline_repo = pipeline_repo

    async def execute(self, pipeline_id: UUID) -> None:
        existing = await self.pipeline_repo.get_by_id(pipeline_id)
        if existing is None:
            raise NotFoundAppError("Pipeline not found")

        await self.pipeline_repo.delete(pipeline_id)
