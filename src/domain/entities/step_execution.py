from dataclasses import dataclass, replace
from datetime import datetime, timezone
from uuid import UUID, uuid4

from src.domain.errors import ValidationError
from src.domain.value_objects.step_execution_status import StepExecutionStatus


@dataclass(slots=True, frozen=True)
class StepExecution:
    id: UUID
    execution_id: UUID
    pipeline_step_id: UUID
    order: int
    status: StepExecutionStatus
    log_output: str | None = None
    exit_code: int | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None

    @staticmethod
    def create(execution_id: str, pipeline_step_id: str, order: int) -> "StepExecution":
        if order < 1:
            raise ValidationError("Order must be greater than or equal to 1")

        return StepExecution(
            id=uuid4(),
            execution_id=UUID(execution_id),
            pipeline_step_id=UUID(pipeline_step_id),
            order=order,
            status=StepExecutionStatus.PENDING,
            log_output=None,
            exit_code=None,
            started_at=None,
            finished_at=None,
        )

    def mark_running(self) -> "StepExecution":
        return replace(
            self,
            status=StepExecutionStatus.RUNNING,
            started_at=self.started_at or datetime.now(timezone.utc),
        )

    def mark_success(self, log_output: str, exit_code: int = 0) -> "StepExecution":
        return replace(
            self,
            status=StepExecutionStatus.SUCCESS,
            log_output=log_output,
            exit_code=exit_code,
            finished_at=datetime.now(timezone.utc),
        )

    def mark_failed(self, log_output: str, exit_code: int) -> "StepExecution":
        return replace(
            self,
            status=StepExecutionStatus.FAILED,
            log_output=log_output,
            exit_code=exit_code,
            finished_at=datetime.now(timezone.utc),
        )

    def mark_skipped(self, log_output: str | None = None) -> "StepExecution":
        return replace(
            self,
            status=StepExecutionStatus.SKIPPED,
            log_output=log_output,
            finished_at=datetime.now(timezone.utc),
        )
