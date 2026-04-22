from src.application import NotFoundAppError, ValidationAppError
from src.application.dtos import ReorderStepsInputDTO
from src.application.dtos.pipeline_dto import PipelineOutputDTO, pipeline_step_to_output_dto
from src.domain.entities.pipeline_step import PipelineStep
from src.domain.ports.repositories import IPipelineRepository


class ReorderSteps:
    def __init__(self, pipeline_repo: IPipelineRepository) -> None:
        self.pipeline_repo = pipeline_repo

    async def execute(self, dto: ReorderStepsInputDTO) -> list[PipelineOutputDTO]:
        pipeline = await self.pipeline_repo.get_by_id(dto.pipeline_id)
        if pipeline is None:
            raise NotFoundAppError("Pipeline not found")

        steps = await self.pipeline_repo.list_steps(dto.pipeline_id)
        existing_ids = {s.id for s in steps}
        requested_ids = set(dto.ordered_step_ids)

        if existing_ids != requested_ids:
            raise ValidationAppError(
                "Ordered step IDs do not match the pipeline's current steps"
            )

        reordered: list[PipelineOutputDTO] = []
        for idx, step_id in enumerate(dto.ordered_step_ids, start=1):
            step = next(s for s in steps if s.id == step_id)
            updated = PipelineStep(
                id=step.id,
                pipeline_id=step.pipeline_id,
                order=idx,
                name=step.name,
                step_type=step.step_type,
                command=step.command,
                on_failure=step.on_failure,
                timeout_seconds=step.timeout_seconds,
                working_directory=step.working_directory,
                is_active=step.is_active,
            )
            saved = await self.pipeline_repo.update_step(updated)
            reordered.append(pipeline_step_to_output_dto(saved))

        return reordered
