from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from src.application.dtos import (
    AddStepInputDTO,
    CreatePipelineInputDTO,
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
from src.application.use_cases.pipelines.update_pipeline import UpdatePipeline
from src.application.use_cases.pipelines.update_step import UpdateStep
from src.interfaces.api.dependencies import (
    CurrentUser,
    get_add_step_use_case,
    get_create_pipeline_use_case,
    get_delete_pipeline_use_case,
    get_delete_step_use_case,
    get_get_pipeline_use_case,
    get_list_pipelines_use_case,
    get_reorder_steps_use_case,
    get_update_pipeline_use_case,
    get_update_step_use_case,
    get_current_user,
    require_admin,
)
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


@router.get(
    "/environments/{environment_id}/pipelines",
    response_model=list[PipelineResponse],
    status_code=status.HTTP_200_OK,
)
async def list_pipelines(
    environment_id: UUID,
    _: Annotated[CurrentUser, Depends(get_current_user)],
    use_case: Annotated[ListPipelines, Depends(get_list_pipelines_use_case)],
) -> list[PipelineResponse]:
    out = await use_case.execute(environment_id)
    return [
        PipelineResponse(
            id=p.id,
            environment_id=p.environment_id,
            name=p.name,
            description=p.description,
        )
        for p in out
    ]


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
    response_model=list[StepResponse],
    status_code=status.HTTP_200_OK,
)
async def get_pipeline(
    pipeline_id: UUID,
    _: Annotated[CurrentUser, Depends(get_current_user)],
    use_case: Annotated[GetPipeline, Depends(get_get_pipeline_use_case)],
) -> list[StepResponse]:
    out = await use_case.execute(pipeline_id)
    return [
        StepResponse(
            id=s.id,
            order=s.order,
            name=s.name,
            step_type=s.step_type,
            command=s.command,
            on_failure=s.on_failure,
            timeout_seconds=s.timeout_seconds,
            working_directory=s.working_directory,
            is_active=s.is_active,
        )
        for s in out
    ]


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
            order=payload.order,
            name=payload.name,
            step_type=payload.step_type,
            command=payload.command,
            on_failure=payload.on_failure,
            timeout_seconds=payload.timeout_seconds,
            working_directory=payload.working_directory,
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
