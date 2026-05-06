"""Utilitário de teste: drena o motor até estado terminal."""

from uuid import UUID

from src.application.dtos import RunNextStepInputDTO
from src.application.use_cases.executions.run_next_step import RunNextStep
from src.domain.entities.execution import Execution
from src.domain.ports.repositories import IExecutionRepository
from src.domain.value_objects.execution_status import ExecutionStatus

_TERMINAL = frozenset(
    {
        ExecutionStatus.SUCCESS,
        ExecutionStatus.FAILED,
        ExecutionStatus.CANCELLED,
        ExecutionStatus.BLOCKED,
    }
)


async def run_next_step_until_terminal(
    execution_repo: IExecutionRepository,
    run_uc: RunNextStep,
    execution_id: UUID,
    *,
    max_rounds: int = 64,
) -> Execution:
    for _ in range(max_rounds):
        ex = await execution_repo.get_by_id(execution_id)
        assert ex is not None
        if ex.status in _TERMINAL:
            return ex
        await run_uc.execute(RunNextStepInputDTO(execution_id=execution_id))
    ex = await execution_repo.get_by_id(execution_id)
    msg = f"execução não terminou após {max_rounds} chamadas"
    if ex is not None:
        msg += f"; status={ex.status}"
    raise AssertionError(msg)
