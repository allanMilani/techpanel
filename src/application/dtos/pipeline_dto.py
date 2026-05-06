from dataclasses import dataclass
from uuid import UUID

from src.domain.entities.pipeline import Pipeline
from src.domain.entities.pipeline_step import PipelineStep


@dataclass(slots=True, frozen=True)
class CreatePipelineInputDTO:
    environment_id: UUID
    name: str
    description: str | None
    created_by: UUID


@dataclass(slots=True, frozen=True)
class AddStepInputDTO:
    pipeline_id: UUID
    name: str
    step_type: str
    command: str
    on_failure: str
    timeout_seconds: int = 300
    working_directory: str | None = None
    order: int | None = None


@dataclass(slots=True, frozen=True)
class PipelineSummaryDTO:
    id: UUID
    environment_id: UUID
    name: str
    description: str | None


@dataclass(slots=True, frozen=True)
class PipelineOutputDTO:
    id: UUID
    order: int
    name: str
    step_type: str
    command: str
    on_failure: str
    timeout_seconds: int
    working_directory: str | None
    is_active: bool


@dataclass(slots=True, frozen=True)
class ReorderStepsInputDTO:
    pipeline_id: UUID
    ordered_step_ids: list[UUID]


@dataclass(slots=True, frozen=True)
class UpdatePipelineInputDTO:
    name: str
    description: str | None


@dataclass(slots=True, frozen=True)
class UpdateStepInputDTO:
    name: str
    step_type: str
    command: str
    on_failure: str
    timeout_seconds: int
    working_directory: str | None
    is_active: bool


def pipeline_step_to_output_dto(step: PipelineStep) -> PipelineOutputDTO:
    return PipelineOutputDTO(
        id=step.id,
        order=step.order,
        name=step.name,
        step_type=step.step_type.value,
        command=step.command,
        on_failure=step.on_failure.value,
        timeout_seconds=step.timeout_seconds,
        working_directory=step.working_directory,
        is_active=step.is_active,
    )


def pipeline_to_summary_dto(pipeline: Pipeline) -> PipelineSummaryDTO:
    return PipelineSummaryDTO(
        id=pipeline.id,
        environment_id=pipeline.environment_id,
        name=pipeline.name,
        description=pipeline.description,
    )
