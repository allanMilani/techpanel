from dataclasses import dataclass, replace
from datetime import UTC, datetime
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
    created_at: datetime
    triggered_by_ip: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    workspace_prepare_log: str | None = None
    workspace_prepare_exit_code: int | None = None

    def with_workspace_prepare(self, log: str | None, exit_code: int | None) -> "Execution":
        return replace(
            self,
            workspace_prepare_log=log,
            workspace_prepare_exit_code=exit_code,
        )

    @staticmethod
    def create(
        pipeline_id: str,
        triggered_by: str,
        branch_or_tag: str,
        triggered_by_ip: str | None = None,
    ) -> "Execution":
        if not pipeline_id:
            raise ValidationError("Pipeline ID is required")

        if not triggered_by:
            raise ValidationError("Triggered by is required")

        if not branch_or_tag.strip():
            raise ValidationError("Branch or tag is required")

        ip: str | None = None
        if triggered_by_ip is not None and triggered_by_ip.strip():
            ip = triggered_by_ip.strip()[:64]

        return Execution(
            id=uuid4(),
            pipeline_id=UUID(pipeline_id),
            triggered_by=UUID(triggered_by),
            branch_or_tag=branch_or_tag.strip(),
            status=ExecutionStatus.PENDING,
            created_at=datetime.now(UTC),
            triggered_by_ip=ip,
            workspace_prepare_log=None,
            workspace_prepare_exit_code=None,
        )

    def mark_running(self) -> "Execution":
        now = datetime.now(UTC)
        return replace(
            self,
            status=ExecutionStatus.RUNNING,
            started_at=self.started_at or now,
        )

    def mark_success(self) -> "Execution":
        now = datetime.now(UTC)
        return replace(
            self,
            status=ExecutionStatus.SUCCESS,
            started_at=self.started_at or now,
            finished_at=self.finished_at or now,
        )

    def mark_failed(self) -> "Execution":
        now = datetime.now(UTC)
        return replace(
            self,
            status=ExecutionStatus.FAILED,
            started_at=self.started_at or now,
            finished_at=self.finished_at or now,
        )

    def mark_cancelled(self) -> "Execution":
        now = datetime.now(UTC)
        return replace(
            self,
            status=ExecutionStatus.CANCELLED,
            finished_at=self.finished_at or now,
        )

    def mark_blocked(self) -> "Execution":
        now = datetime.now(UTC)
        return replace(
            self,
            status=ExecutionStatus.BLOCKED,
            finished_at=self.finished_at or now,
        )
