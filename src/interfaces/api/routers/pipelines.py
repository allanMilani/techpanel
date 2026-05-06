from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.application.dtos import (
    AddStepInputDTO,
    CreatePipelineInputDTO,
    ExecutionOutputDTO,
    ReorderStepsInputDTO,
    UpdatePipelineInputDTO,
    UpdateStepInputDTO,
)
from src.application.use_cases.pipelines.add_step import AddStep
from src.application.use_cases.pipelines.create_pipeline import CreatePipeline
from src.application.use_cases.pipelines.delete_pipeline import DeletePipeline
from src.application.use_cases.pipelines.delete_step import DeleteStep
from src.application.use_cases.pipelines.get_pipeline import GetPipeline
from src.application.use_cases.pipelines.list_pipelines import ListPipelines
from src.application.use_cases.pipelines.reorder_steps import ReorderSteps
from src.application.use_cases.executions.get_history import GetHistory
from src.application.use_cases.pipelines.update_pipeline import UpdatePipeline
from src.application.use_cases.pipelines.update_step import UpdateStep
from src.domain.ports.repositories import IPipelineRepository
from src.interfaces.api.dependencies import (
    CurrentUser,
    get_add_step_use_case,
    get_create_pipeline_use_case,
    get_delete_pipeline_use_case,
    get_delete_step_use_case,
    get_get_history_use_case,
    get_get_pipeline_use_case,
    get_list_pipelines_use_case,
    get_reorder_steps_use_case,
    get_update_pipeline_use_case,
    get_update_step_use_case,
    get_current_user,
    require_admin,
)
from src.interfaces.api.dependencies.pagination import Pagination, get_pagination
from src.interfaces.api.schemas.paged_lists import (
    ExecutionHistoryPageResponse,
    PipelineStepsPageResponse,
    PipelinesListPageResponse,
)
from src.interfaces.api.dependencies.core import (
    get_environment_repository,
    get_pipeline_repository,
)
from src.interfaces.api.schemas import ExecutionResponse
from src.interfaces.api.schemas.pipelines import (
    PipelineCreateRequest,
    PipelineResponse,
    PipelineUpdateRequest,
    ReorderStepsRequest,
    StepCreateRequest,
    StepResponse,
    StepUpdateRequest,
)

router = APIRouter(tags=["pipelines"])


def _step_response_from_output(out) -> StepResponse:
    return StepResponse(
        id=out.id,
        order=out.order,
        name=out.name,
        step_type=out.step_type,
        command=out.command,
        on_failure=out.on_failure,
        timeout_seconds=out.timeout_seconds,
        working_directory=out.working_directory,
        is_active=out.is_active,
    )


def _history_item_to_response(item: ExecutionOutputDTO) -> ExecutionResponse:
    return ExecutionResponse(
        id=str(item.id),
        pipeline_id=str(item.pipeline_id),
        branch_or_tag=item.branch_or_tag,
        status=item.status,
        created_at=item.created_at,
    )


@router.get(
    "/pipelines/{pipeline_id}/summary",
    response_model=PipelineResponse,
    status_code=status.HTTP_200_OK,
)
async def get_pipeline_summary(
    pipeline_id: UUID,
    _: Annotated[CurrentUser, Depends(get_current_user)],
    repo: Annotated[IPipelineRepository, Depends(get_pipeline_repository)],
    env_repo: Annotated[object, Depends(get_environment_repository)],
) -> PipelineResponse:
    pipeline = await repo.get_by_id(pipeline_id)
    if pipeline is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    env = await env_repo.get_by_id(pipeline.environment_id)
    project_id = env.project_id if env is not None else None
    return PipelineResponse(
        id=pipeline.id,
        environment_id=pipeline.environment_id,
        name=pipeline.name,
        description=pipeline.description,
        project_id=project_id,
    )


@router.get(
    "/pipelines/{pipeline_id}/history",
    response_model=ExecutionHistoryPageResponse,
    status_code=status.HTTP_200_OK,
)
async def get_pipeline_history(
    pipeline_id: UUID,
    _: Annotated[CurrentUser, Depends(get_current_user)],
    pagination: Annotated[Pagination, Depends(get_pagination)],
    history_uc: Annotated[GetHistory, Depends(get_get_history_use_case)],
) -> ExecutionHistoryPageResponse:
    out = await history_uc.execute(pipeline_id, pagination.page, pagination.per_page)
    return ExecutionHistoryPageResponse(
        items=[_history_item_to_response(h) for h in out.items],
        total=out.total,
        page=out.page,
        per_page=out.per_page,
        total_pages=out.total_pages,
    )


@router.get(
    "/environments/{environment_id}/pipelines",
    response_model=PipelinesListPageResponse,
    status_code=status.HTTP_200_OK,
)
async def list_pipelines(
    environment_id: UUID,
    _: Annotated[CurrentUser, Depends(get_current_user)],
    pagination: Annotated[Pagination, Depends(get_pagination)],
    use_case: Annotated[ListPipelines, Depends(get_list_pipelines_use_case)],
) -> PipelinesListPageResponse:
    out = await use_case.execute(environment_id, pagination.page, pagination.per_page)
    return PipelinesListPageResponse(
        items=[
            PipelineResponse(
                id=p.id,
                environment_id=p.environment_id,
                name=p.name,
                description=p.description,
            )
            for p in out.items
        ],
        total=out.total,
        page=out.page,
        per_page=out.per_page,
        total_pages=out.total_pages,
    )


@router.post(
    "/environments/{environment_id}/pipelines",
    response_model=PipelineResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_pipeline(
    environment_id: UUID,
    payload: PipelineCreateRequest,
    current_user: Annotated[CurrentUser, Depends(require_admin)],
    use_case: Annotated[CreatePipeline, Depends(get_create_pipeline_use_case)],
) -> PipelineResponse:
    out = await use_case.execute(
        CreatePipelineInputDTO(
            environment_id=environment_id,
            name=payload.name,
            description=payload.description,
            created_by=UUID(current_user.sub),
        )
    )
    return PipelineResponse(
        id=out.id,
        environment_id=out.environment_id,
        name=out.name,
        description=out.description,
    )


@router.get(
    "/pipelines/{pipeline_id}",
    response_model=PipelineStepsPageResponse,
    status_code=status.HTTP_200_OK,
)
async def get_pipeline(
    pipeline_id: UUID,
    _: Annotated[CurrentUser, Depends(get_current_user)],
    pagination: Annotated[Pagination, Depends(get_pagination)],
    use_case: Annotated[GetPipeline, Depends(get_get_pipeline_use_case)],
) -> PipelineStepsPageResponse:
    out = await use_case.execute(pipeline_id, pagination.page, pagination.per_page)
    return PipelineStepsPageResponse(
        items=[_step_response_from_output(s) for s in out.items],
        total=out.total,
        page=out.page,
        per_page=out.per_page,
        total_pages=out.total_pages,
    )


@router.put(
    "/pipelines/{pipeline_id}",
    response_model=PipelineResponse,
    status_code=status.HTTP_200_OK,
)
async def update_pipeline(
    pipeline_id: UUID,
    payload: PipelineUpdateRequest,
    _: Annotated[CurrentUser, Depends(require_admin)],
    use_case: Annotated[UpdatePipeline, Depends(get_update_pipeline_use_case)],
) -> PipelineResponse:
    out = await use_case.execute(
        pipeline_id,
        UpdatePipelineInputDTO(
            name=payload.name,
            description=payload.description,
        ),
    )
    return PipelineResponse(
        id=out.id,
        environment_id=out.environment_id,
        name=out.name,
        description=out.description,
    )


@router.delete(
    "/pipelines/{pipeline_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_pipeline(
    pipeline_id: UUID,
    _: Annotated[CurrentUser, Depends(require_admin)],
    use_case: Annotated[DeletePipeline, Depends(get_delete_pipeline_use_case)],
) -> None:
    await use_case.execute(pipeline_id)


@router.post(
    "/pipelines/{pipeline_id}/steps",
    response_model=StepResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_step(
    pipeline_id: UUID,
    payload: StepCreateRequest,
    _: Annotated[CurrentUser, Depends(require_admin)],
    use_case: Annotated[AddStep, Depends(get_add_step_use_case)],
) -> StepResponse:
    out = await use_case.execute(
        AddStepInputDTO(
            pipeline_id=pipeline_id,
            name=payload.name,
            step_type=payload.step_type,
            command=payload.command,
            on_failure=payload.on_failure,
            timeout_seconds=payload.timeout_seconds,
            working_directory=payload.working_directory,
            order=payload.order,
        )
    )
    return _step_response_from_output(out)


@router.put(
    "/pipelines/{pipeline_id}/steps/{step_id}",
    response_model=StepResponse,
    status_code=status.HTTP_200_OK,
)
async def update_step(
    pipeline_id: UUID,
    step_id: UUID,
    payload: StepUpdateRequest,
    _: Annotated[CurrentUser, Depends(require_admin)],
    use_case: Annotated[UpdateStep, Depends(get_update_step_use_case)],
) -> StepResponse:
    out = await use_case.execute(
        pipeline_id,
        step_id,
        UpdateStepInputDTO(
            name=payload.name,
            step_type=payload.step_type,
            command=payload.command,
            on_failure=payload.on_failure,
            timeout_seconds=payload.timeout_seconds,
            working_directory=payload.working_directory,
            is_active=payload.is_active,
        ),
    )
    return _step_response_from_output(out)


@router.delete(
    "/pipelines/{pipeline_id}/steps/{step_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_step(
    pipeline_id: UUID,
    step_id: UUID,
    _: Annotated[CurrentUser, Depends(require_admin)],
    use_case: Annotated[DeleteStep, Depends(get_delete_step_use_case)],
) -> None:
    await use_case.execute(pipeline_id, step_id)


@router.post(
    "/pipelines/{pipeline_id}/steps/reorder",
    response_model=list[StepResponse],
    status_code=status.HTTP_200_OK,
)
async def reorder_steps(
    pipeline_id: UUID,
    payload: ReorderStepsRequest,
    _: Annotated[CurrentUser, Depends(require_admin)],
    use_case: Annotated[ReorderSteps, Depends(get_reorder_steps_use_case)],
) -> list[StepResponse]:
    out = await use_case.execute(
        ReorderStepsInputDTO(
            pipeline_id=pipeline_id,
            ordered_step_ids=payload.ordered_step_ids,
        )
    )
    return [_step_response_from_output(step) for step in out]
