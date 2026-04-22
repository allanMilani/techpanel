from src.application import NotFoundAppError
from src.application.dtos import AddStepInputDTO, PipelineOutputDTO
from src.application.dtos.pipeline_dto import pipeline_step_to_output_dto
from src.domain.entities import PipelineStep
from src.domain.ports.repositories import IPipelineRepository
from src.domain.value_objects.on_failure_policy import OnFailurePolicy
from src.domain.value_objects.step_type import StepType


class AddStep:
    def __init__(self, pipeline_repo: IPipelineRepository) -> None:
        self.pipeline_repo = pipeline_repo

    async def execute(self, dto: AddStepInputDTO) -> PipelineOutputDTO:
        pipeline = await self.pipeline_repo.get_by_id(dto.pipeline_id)
        if pipeline is None:
            raise NotFoundAppError("Pipeline not found")

        step = PipelineStep.create(
            pipeline_id=str(dto.pipeline_id),
            order=dto.order,
            name=dto.name,
            step_type=StepType(dto.step_type),
            command=dto.command,
            on_failure=OnFailurePolicy(dto.on_failure),
        )

        created = await self.pipeline_repo.add_step(step)
        return pipeline_step_to_output_dto(created)
