from src.domain.entities.step_execution import StepExecution
from src.domain.value_objects.step_execution_status import StepExecutionStatus


def test_deve_iniciar_com_pending() -> None:
    step_exec = StepExecution.create(
        execution_id="00000000-0000-0000-0000-000000000001",
        pipeline_step_id="00000000-0000-0000-0000-000000000002",
        order=1,
    )
    assert step_exec.status == StepExecutionStatus.PENDING


def test_deve_transicionar_para_success() -> None:
    step_exec = StepExecution.create(
        execution_id="00000000-0000-0000-0000-000000000001",
        pipeline_step_id="00000000-0000-0000-0000-000000000002",
        order=1,
    )
    done = step_exec.mark_success("ok", 0)
    assert done.status == StepExecutionStatus.SUCCESS
    assert done.exit_code == 0
