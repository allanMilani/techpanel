from dataclasses import replace
from uuid import UUID
from src.application import NotFoundAppError
from src.application.dtos import PipelineOutputDTO, UpdateStepInputDTO
from src.application.dtos.pipeline_dto import pipeline_step_to_output_dto
from src.domain.ports.repositories import IPipelineRepository
from src.domain.value_objects.on_failure_policy import OnFailurePolicy
from src.domain.value_objects.step_type import StepType


class UpdateStep:
    def __init__(
        self,
        pipeline_repo: IPipelineRepository,
    ) -> None:
        self.pipeline_repo = pipeline_repo

    async def execute(
        self, pipeline_id: UUID, step_id: UUID, dto: UpdateStepInputDTO
    ) -> PipelineOutputDTO:
        pipeline = await self.pipeline_repo.get_by_id(pipeline_id)
        if pipeline is None:
            raise NotFoundAppError("Pipeline not found")

        steps = await self.pipeline_repo.list_steps(pipeline_id)
        step = next((s for s in steps if s.id == step_id), None)
        if step is None:
            raise NotFoundAppError("Pipeline step not found")

        updated = replace(
            step,
            name=dto.name.strip(),
            step_type=StepType(dto.step_type),
            command=dto.command.strip(),
            on_failure=OnFailurePolicy(dto.on_failure),
            timeout_seconds=dto.timeout_seconds,
            working_directory=dto.working_directory,
            is_active=dto.is_active,
        )
        persisted = await self.pipeline_repo.update_step(updated)
        return pipeline_step_to_output_dto(persisted)
