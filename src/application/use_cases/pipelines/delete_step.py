from uuid import UUID
from src.application import NotFoundAppError
from src.domain.ports.repositories import IPipelineRepository


class DeleteStep:
    def __init__(
        self,
        pipeline_repo: IPipelineRepository,
    ) -> None:
        self.pipeline_repo = pipeline_repo

    async def execute(self, pipeline_id: UUID, step_id: UUID) -> None:
        existing = await self.pipeline_repo.get_by_id(pipeline_id)
        if existing is None:
            raise NotFoundAppError("Pipeline not found")

        steps = await self.pipeline_repo.list_steps(pipeline_id)
        step = next((s for s in steps if s.id == step_id), None)
        if step is None:
            raise NotFoundAppError("Pipeline step not found")

        await self.pipeline_repo.remove_step(step_id)
