from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from src.application.dtos import (
    ExecutionOutputDTO,
    RunNextStepInputDTO,
    StartExecutionInputDTO,
)
from src.domain.entities.execution import Execution as DomainExecution
from src.application.errors import NotFoundAppError
from src.application.use_cases.executions.get_execution_logs import GetExecutionLogs
from src.application.use_cases.executions.cancel_execution import CancelExecution
from src.application.use_cases.executions.run_next_step import RunNextStep
from src.application.use_cases.executions.start_execution import StartExecution
from src.application.use_cases.pipelines.get_pipeline import GetPipeline
from src.domain.ports.repositories import IPipelineRepository
from src.domain.value_objects.execution_status import ExecutionStatus
from src.interfaces.api.dependencies.core import get_pipeline_repository
from src.interfaces.api.dependencies import (
    CurrentUser,
    get_cancel_execution_use_case,
    get_current_user,
    get_execution_repository,
    get_get_execution_logs_use_case,
    get_get_pipeline_use_case,
    get_run_next_step_use_case,
    get_start_execution_use_case,
    require_admin,
)
from src.interfaces.api.schemas import (
    ExecutionPanelResponse,
    ExecutionResponse,
    StartExecutionRequest,
    StepExecutionResponse,
)

router = APIRouter(prefix="/executions", tags=["executions"])


def _client_host(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()[:64] or None
    if request.client:
        return (request.client.host or "")[:64] or None
    return None


def _execution_is_terminal(status: str) -> bool:
    return status in (
        ExecutionStatus.SUCCESS.value,
        ExecutionStatus.FAILED.value,
        ExecutionStatus.BLOCKED.value,
        ExecutionStatus.CANCELLED.value,
    )


def _execution_to_response(
    execution: DomainExecution | ExecutionOutputDTO,
) -> ExecutionResponse:
    status_str = (
        execution.status
        if isinstance(execution, ExecutionOutputDTO)
        else execution.status.value
    )
    return ExecutionResponse(
        id=str(execution.id),
        pipeline_id=str(execution.pipeline_id),
        branch_or_tag=execution.branch_or_tag,
        status=status_str,
        created_at=execution.created_at,
    )


def _step_log_to_response(
    dto: object,
    step_commands: dict[str, str],
) -> StepExecutionResponse:
    pid = dto.pipeline_step_id
    if pid is None:
        return StepExecutionResponse(
            id=str(dto.id),
            execution_id=str(dto.execution_id),
            pipeline_step_id=None,
            order=dto.order,
            status=dto.status,
            log_output=dto.log_output,
            exit_code=dto.exit_code,
            command=None,
        )
    ps = str(pid)
    return StepExecutionResponse(
        id=str(dto.id),
        execution_id=str(dto.execution_id),
        pipeline_step_id=ps,
        order=dto.order,
        status=dto.status,
        log_output=dto.log_output,
        exit_code=dto.exit_code,
        command=step_commands.get(ps),
    )


@router.get(
    "/{execution_id}",
    response_model=ExecutionResponse,
    status_code=status.HTTP_200_OK,
)
async def get_execution(
    execution_id: UUID,
    _: Annotated[CurrentUser, Depends(get_current_user)],
    exec_repo: Annotated[object, Depends(get_execution_repository)],
) -> ExecutionResponse:
    execution = await exec_repo.get_by_id(execution_id)
    if execution is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return _execution_to_response(execution)


@router.get(
    "/{execution_id}/panel",
    response_model=ExecutionPanelResponse,
    status_code=status.HTTP_200_OK,
)
async def get_execution_panel(
    execution_id: UUID,
    _: Annotated[CurrentUser, Depends(get_current_user)],
    exec_repo: Annotated[object, Depends(get_execution_repository)],
    logs_uc: Annotated[GetExecutionLogs, Depends(get_get_execution_logs_use_case)],
    get_pipeline_uc: Annotated[GetPipeline, Depends(get_get_pipeline_use_case)],
    pipeline_repo: Annotated[IPipelineRepository, Depends(get_pipeline_repository)],
) -> ExecutionPanelResponse:
    execution = await exec_repo.get_by_id(execution_id)
    if execution is None:
        return ExecutionPanelResponse(
            error="Execução não encontrada",
            execution=None,
            step_logs=[],
            step_labels={},
            terminal=True,
        )
    try:
        steps = await get_pipeline_uc.execute_all_steps(execution.pipeline_id)
    except NotFoundAppError:
        steps = []
    step_labels = {str(s.id): s.name for s in steps}
    step_commands = {str(s.id): s.command for s in steps}
    try:
        step_logs_dto = await logs_uc.execute(execution_id)
    except NotFoundAppError:
        step_logs_dto = []
    step_logs = [_step_log_to_response(s, step_commands) for s in step_logs_dto]
    terminal = _execution_is_terminal(execution.status.value)
    pipeline = await pipeline_repo.get_by_id(execution.pipeline_id)
    prep_skipped = bool(
        pipeline is not None
        and not pipeline.run_git_workspace_sync
        and execution.workspace_prepare_exit_code is not None
        and execution.workspace_prepare_exit_code == 0
    )
    return ExecutionPanelResponse(
        error=None,
        execution=_execution_to_response(execution),
        step_logs=step_logs,
        step_labels=step_labels,
        terminal=terminal,
        workspace_prepare_log=execution.workspace_prepare_log,
        workspace_prepare_exit_code=execution.workspace_prepare_exit_code,
        workspace_prepare_skipped=prep_skipped,
    )


@router.post(
    "/start", response_model=ExecutionResponse, status_code=status.HTTP_201_CREATED
)
async def start_execution(
    request: Request,
    payload: StartExecutionRequest,
    current_user: Annotated[CurrentUser, Depends(require_admin)],
    use_case: Annotated[StartExecution, Depends(get_start_execution_use_case)],
) -> ExecutionResponse:
    out = await use_case.execute(
        StartExecutionInputDTO(
            pipeline_id=UUID(payload.pipeline_id),
            triggered_by=UUID(current_user.sub),
            branch_or_tag=payload.branch_or_tag,
            triggered_by_ip=_client_host(request),
        )
    )

    return _execution_to_response(out)


@router.post(
    "/{execution_id}/next-step",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def run_next_step(
    execution_id: UUID,
    _current_user: Annotated[CurrentUser, Depends(require_admin)],
    use_case: Annotated[RunNextStep, Depends(get_run_next_step_use_case)],
) -> None:
    await use_case.execute(RunNextStepInputDTO(execution_id=execution_id))


@router.post(
    "/{execution_id}/cancel",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def cancel_execution(
    execution_id: UUID,
    _current_user: Annotated[CurrentUser, Depends(require_admin)],
    use_case: Annotated[CancelExecution, Depends(get_cancel_execution_use_case)],
) -> None:
    await use_case.execute(execution_id)
