from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.domain.entities.execution import Execution
from src.domain.entities.step_execution import StepExecution


@dataclass(slots=True, frozen=True)
class StartExecutionInputDTO:
    pipeline_id: UUID
    triggered_by: UUID
    branch_or_tag: str
    triggered_by_ip: str | None = None


@dataclass(slots=True, frozen=True)
class ExecutionOutputDTO:
    id: UUID
    pipeline_id: UUID
    status: str
    branch_or_tag: str
    created_at: datetime


@dataclass(slots=True, frozen=True)
class RunNextStepInputDTO:
    execution_id: UUID


@dataclass(slots=True, frozen=True)
class StepExecutionOutputDTO:
    id: UUID
    execution_id: UUID
    pipeline_step_id: UUID
    order: int
    status: str
    log_output: str | None
    exit_code: int | None


def execution_to_output_dto(execution: Execution) -> ExecutionOutputDTO:
    return ExecutionOutputDTO(
        id=execution.id,
        pipeline_id=execution.pipeline_id,
        status=execution.status.value,
        branch_or_tag=execution.branch_or_tag,
        created_at=execution.created_at,
    )


def step_execution_to_output_dto(step: StepExecution) -> StepExecutionOutputDTO:
    return StepExecutionOutputDTO(
        id=step.id,
        execution_id=step.execution_id,
        pipeline_step_id=step.pipeline_step_id,
        order=step.order,
        status=step.status.value,
        log_output=step.log_output,
        exit_code=step.exit_code,
    )
