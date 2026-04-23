from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from src.application.dtos import StartExecutionInputDTO
from src.application.use_cases.executions.start_execution import StartExecution
from src.interfaces.api.dependencies import CurrentUser, require_admin
from src.interfaces.api.schemas import StartExecutionRequest, ExecutionResponse
from src.interfaces.api.dependencies import get_start_execution_use_case

router = APIRouter(prefix="/executions", tags=["executions"])


@router.post(
    "/start", response_model=ExecutionResponse, status_code=status.HTTP_201_CREATED
)
async def start_execution(
    payload: StartExecutionRequest,
    current_user: Annotated[CurrentUser, Depends(require_admin)],
    use_case: Annotated[StartExecution, Depends(get_start_execution_use_case)],
) -> ExecutionResponse:
    out = await use_case.execute(
        StartExecutionInputDTO(
            pipeline_id=UUID(payload.pipeline_id),
            triggered_by=UUID(current_user.sub),
            branch_or_tag=payload.branch_or_tag,
        )
    )

    return ExecutionResponse(
        id=str(out.id),
        pipeline_id=str(out.pipeline_id),
        branch_or_tag=out.branch_or_tag,
        status=out.status,
    )
