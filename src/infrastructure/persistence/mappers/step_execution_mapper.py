from __future__ import annotations

from src.domain.entities.step_execution import StepExecution
from src.domain.value_objects.step_execution_status import StepExecutionStatus
from src.infrastructure.persistence.models.step_execution_model import (
    StepExecutionModel,
)


def step_execution_model_to_entity(row: StepExecutionModel) -> StepExecution:
    return StepExecution(
        id=row.id,
        execution_id=row.execution_id,
        pipeline_step_id=row.pipeline_step_id,
        order=row.order,
        status=StepExecutionStatus(
            row.status.value if hasattr(row.status, "value") else str(row.status)
        ),
        log_output=row.log_output,
        exit_code=row.exit_code,
        started_at=row.started_at,
        finished_at=row.finished_at,
    )
