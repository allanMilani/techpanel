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
        created_at=row.created_at,
        triggered_by_ip=row.triggered_by_ip,
        started_at=row.started_at,
        finished_at=row.finished_at,
        workspace_prepare_log=getattr(row, "workspace_prepare_log", None),
        workspace_prepare_exit_code=getattr(row, "workspace_prepare_exit_code", None),
    )
