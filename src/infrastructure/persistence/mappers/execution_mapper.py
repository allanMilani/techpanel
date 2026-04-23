from __future__ import annotations

from src.domain.entities.execution import Execution
from src.domain.value_objects.execution_status import ExecutionStatus
from src.infrastructure.persistence.models.execution_model import ExecutionModel


def execution_model_to_entity(row: ExecutionModel) -> Execution:
    return Execution(
        id=row.id,
        pipeline_id=row.pipeline_id,
        triggered_by=row.triggered_by,
        branch_or_tag=row.branch_or_tag,
        status=ExecutionStatus(
            row.status.value if hasattr(row.status, "value") else str(row.status)
        ),
    )
