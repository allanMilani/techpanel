from dataclasses import dataclass, replace
from uuid import UUID, uuid4

from src.domain.errors import ValidationError
from src.domain.value_objects.execution_status import ExecutionStatus

@dataclass(slots=True, frozen=True)
class Execution:
    id: UUID
    pipeline_id: UUID
    triggered_by: UUID
    branch_or_tag: str
    status: ExecutionStatus

    @staticmethod
    def create(pipeline_id: str, triggered_by: str, branch_or_tag: str) -> "Execution":
        if not pipeline_id:
            raise ValidationError("Pipeline ID is required")

        if not triggered_by:
            raise ValidationError("Triggered by is required")

        if not branch_or_tag.strip():
            raise ValidationError("Branch or tag is required")

        return Execution(
            id=uuid4(),
            pipeline_id=UUID(pipeline_id),
            triggered_by=UUID(triggered_by),
            branch_or_tag=branch_or_tag.strip(),
            status=ExecutionStatus.PENDING,
        )

    def mark_running(self) -> "Execution":
        return replace(self, status=ExecutionStatus.RUNNING)