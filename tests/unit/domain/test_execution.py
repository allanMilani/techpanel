from src.domain.entities.execution import Execution
from src.domain.value_objects.execution_status import ExecutionStatus


def test_should_start_with_pending_status() -> None:
    execution = Execution.create(
        pipeline_id="00000000-0000-0000-0000-000000000001",
        triggered_by="00000000-0000-0000-0000-000000000002",
        branch_or_tag="main",
    )
    assert execution.status == ExecutionStatus.PENDING