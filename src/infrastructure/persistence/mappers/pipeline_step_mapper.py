from __future__ import annotations

from src.domain.entities.pipeline_step import PipelineStep
from src.domain.value_objects.on_failure_policy import OnFailurePolicy
from src.domain.value_objects.step_type import StepType
from src.infrastructure.persistence.models.pipeline_step_model import PipelineStepModel


def pipeline_step_model_to_entity(row: PipelineStepModel) -> PipelineStep:
    return PipelineStep(
        id=row.id,
        pipeline_id=row.pipeline_id,
        order=row.order,
        name=row.name,
        step_type=StepType(
            row.type.value if hasattr(row.type, "value") else str(row.type)
        ),
        command=row.command,
        on_failure=OnFailurePolicy(
            row.on_failure.value
            if hasattr(row.on_failure, "value")
            else str(row.on_failure)
        ),
        timeout_seconds=row.timeout_seconds,
        working_directory=row.working_directory,
        is_active=row.is_active,
    )


def pipeline_step_entity_fields_for_insert(step: PipelineStep) -> dict:
    return {
        "id": step.id,
        "pipeline_id": step.pipeline_id,
        "order": step.order,
        "name": step.name,
        "type": step.step_type.value,
        "command": step.command,
        "working_directory": step.working_directory,
        "timeout_seconds": step.timeout_seconds,
        "on_failure": step.on_failure.value,
        "is_active": step.is_active,
    }
