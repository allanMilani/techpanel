from datetime import UTC

from src.domain.entities.execution import Execution
from src.domain.value_objects.execution_status import ExecutionStatus


def test_should_start_with_pending_status() -> None:
    execution = Execution.create(
        pipeline_id="00000000-0000-0000-0000-000000000001",
        triggered_by="00000000-0000-0000-0000-000000000002",
        branch_or_tag="main",
        triggered_by_ip="203.0.113.1",
    )
    assert execution.status == ExecutionStatus.PENDING
    assert execution.created_at.tzinfo == UTC
    assert execution.triggered_by_ip == "203.0.113.1"
    assert execution.started_at is None
    assert execution.finished_at is None


def test_mark_success_and_mark_failed() -> None:
    execution = Execution.create(
        pipeline_id="00000000-0000-0000-0000-000000000001",
        triggered_by="00000000-0000-0000-0000-000000000002",
        branch_or_tag="main",
    )
    ok = execution.mark_success()
    assert ok.status == ExecutionStatus.SUCCESS
    assert ok.created_at == execution.created_at
    assert ok.started_at is not None
    assert ok.finished_at is not None

    running = execution.mark_running()
    assert running.started_at is not None
    assert running.finished_at is None

    failed = execution.mark_failed()
    assert failed.status == ExecutionStatus.FAILED
    assert failed.started_at is not None
    assert failed.finished_at is not None

    cancelled = execution.mark_cancelled()
    assert cancelled.status == ExecutionStatus.CANCELLED
    assert cancelled.finished_at is not None
