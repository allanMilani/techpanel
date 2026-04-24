from uuid import uuid4

import pytest

from src.application import NotFoundAppError
from src.application.dtos import (
    AddStepInputDTO,
    ReorderStepsInputDTO,
    UpdateStepInputDTO,
)
from src.application.use_cases.pipelines.add_step import AddStep
from src.application.use_cases.pipelines.delete_step import DeleteStep
from src.application.use_cases.pipelines.get_pipeline import GetPipeline
from src.application.use_cases.pipelines.reorder_steps import ReorderSteps
from src.application.use_cases.pipelines.update_step import UpdateStep
from src.domain.entities.pipeline import Pipeline
from src.domain.value_objects.on_failure_policy import OnFailurePolicy
from src.domain.value_objects.step_type import StepType
from tests.unit.application.fakes import MemoryPipelineRepo


@pytest.mark.asyncio
async def test_step_crud_and_reorder_with_three_steps() -> None:
    pipeline = Pipeline.create(name="deploy", environment_id=str(uuid4()))
    repo = MemoryPipelineRepo(pipeline, [])

    add_uc = AddStep(repo)
    s1 = await add_uc.execute(
        AddStepInputDTO(
            pipeline_id=pipeline.id,
            order=1,
            name="pull",
            step_type=StepType.SSH_COMMAND.value,
            command="git pull",
            on_failure=OnFailurePolicy.STOP.value,
            timeout_seconds=120,
            working_directory="/srv/app",
        )
    )
    s2 = await add_uc.execute(
        AddStepInputDTO(
            pipeline_id=pipeline.id,
            order=2,
            name="health",
            step_type=StepType.HTTP_HEALTHCHECK.value,
            command="https://api/health",
            on_failure=OnFailurePolicy.CONTINUE.value,
            timeout_seconds=30,
            working_directory=None,
        )
    )
    s3 = await add_uc.execute(
        AddStepInputDTO(
            pipeline_id=pipeline.id,
            order=3,
            name="notify",
            step_type=StepType.NOTIFY_WEBHOOK.value,
            command="https://hooks/notify",
            on_failure=OnFailurePolicy.NOTIFY_AND_STOP.value,
            timeout_seconds=20,
            working_directory=None,
        )
    )

    update_uc = UpdateStep(repo)
    updated_s2 = await update_uc.execute(
        pipeline.id,
        s2.id,
        UpdateStepInputDTO(
            name="healthcheck",
            step_type=StepType.HTTP_HEALTHCHECK.value,
            command="https://api/v2/health",
            on_failure=OnFailurePolicy.STOP.value,
            timeout_seconds=45,
            working_directory=None,
            is_active=True,
        ),
    )
    assert updated_s2.name == "healthcheck"
    assert updated_s2.timeout_seconds == 45

    reorder_uc = ReorderSteps(repo)
    reordered = await reorder_uc.execute(
        ReorderStepsInputDTO(
            pipeline_id=pipeline.id,
            ordered_step_ids=[s3.id, s1.id, s2.id],
        )
    )
    assert [x.order for x in reordered] == [1, 2, 3]
    assert [x.id for x in reordered] == [s3.id, s1.id, s2.id]
    assert len(reordered) == 3

    get_uc = GetPipeline(repo)
    relido = await get_uc.execute(pipeline.id)
    assert len(relido) == 3
    assert [x.order for x in relido] == [1, 2, 3]
    assert [x.id for x in relido] == [s3.id, s1.id, s2.id]
    assert {x.step_type for x in relido} == {
        StepType.SSH_COMMAND.value,
        StepType.HTTP_HEALTHCHECK.value,
        StepType.NOTIFY_WEBHOOK.value,
    }

    delete_uc = DeleteStep(repo)
    await delete_uc.execute(pipeline.id, s1.id)
    remaining = await repo.list_steps(pipeline.id)
    assert len(remaining) == 2
    assert {s.id for s in remaining} == {s2.id, s3.id}


@pytest.mark.asyncio
async def test_update_step_not_found() -> None:
    pipeline = Pipeline.create(name="deploy", environment_id=str(uuid4()))
    repo = MemoryPipelineRepo(pipeline, [])
    use_case = UpdateStep(repo)

    with pytest.raises(NotFoundAppError):
        await use_case.execute(
            pipeline.id,
            uuid4(),
            UpdateStepInputDTO(
                name="x",
                step_type=StepType.SSH_COMMAND.value,
                command="echo",
                on_failure=OnFailurePolicy.STOP.value,
                timeout_seconds=10,
                working_directory=None,
                is_active=True,
            ),
        )
