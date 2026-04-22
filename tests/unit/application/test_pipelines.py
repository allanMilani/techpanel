from uuid import uuid4

import pytest

from src.application import NotFoundAppError, ValidationAppError
from src.application.dtos import AddStepInputDTO, CreatePipelineInputDTO, ReorderStepsInputDTO
from src.application.use_cases.pipelines.add_step import AddStep
from src.application.use_cases.pipelines.create_pipeline import CreatePipeline
from src.application.use_cases.pipelines.reorder_steps import ReorderSteps
from src.domain.entities.pipeline import Pipeline
from src.domain.entities.pipeline_step import PipelineStep
from src.domain.value_objects.on_failure_policy import OnFailurePolicy
from src.domain.value_objects.step_type import StepType

from tests.unit.application.fakes import MemoryPipelineRepo


@pytest.mark.asyncio
async def test_create_pipeline_returns_summary() -> None:
    repo = MemoryPipelineRepo()
    use_case = CreatePipeline(repo)
    env_id = uuid4()
    uid = uuid4()
    out = await use_case.execute(
        CreatePipelineInputDTO(
            environment_id=env_id,
            name="Deploy",
            description=None,
            created_by=uid,
        )
    )
    assert out.environment_id == env_id
    assert out.name == "Deploy"


@pytest.mark.asyncio
async def test_add_step_returns_output_dto() -> None:
    p = Pipeline.create("p", str(uuid4()))
    repo = MemoryPipelineRepo(p, [])
    use_case = AddStep(repo)
    out = await use_case.execute(
        AddStepInputDTO(
            pipeline_id=p.id,
            order=1,
            name="pull",
            step_type=StepType.SSH_COMMAND.value,
            command="git pull",
            on_failure=OnFailurePolicy.STOP.value,
        )
    )
    assert out.order == 1
    assert out.step_type == StepType.SSH_COMMAND.value


@pytest.mark.asyncio
async def test_add_step_pipeline_not_found() -> None:
    repo = MemoryPipelineRepo()
    use_case = AddStep(repo)
    with pytest.raises(NotFoundAppError):
        await use_case.execute(
            AddStepInputDTO(
                pipeline_id=uuid4(),
                order=1,
                name="x",
                step_type=StepType.SSH_COMMAND.value,
                command="c",
                on_failure=OnFailurePolicy.STOP.value,
            )
        )


@pytest.mark.asyncio
async def test_reorder_steps_success() -> None:
    p = Pipeline.create("p", str(uuid4()))
    s1 = PipelineStep.create(
        str(p.id),
        1,
        "a",
        StepType.SSH_COMMAND,
        "echo 1",
        OnFailurePolicy.STOP,
    )
    s2 = PipelineStep.create(
        str(p.id),
        2,
        "b",
        StepType.SSH_COMMAND,
        "echo 2",
        OnFailurePolicy.STOP,
    )
    repo = MemoryPipelineRepo(p, [s1, s2])
    use_case = ReorderSteps(repo)
    out = await use_case.execute(
        ReorderStepsInputDTO(pipeline_id=p.id, ordered_step_ids=[s2.id, s1.id])
    )
    assert [x.order for x in out] == [1, 2]
    assert {x.id for x in out} == {s1.id, s2.id}


@pytest.mark.asyncio
async def test_reorder_steps_invalid_id_set() -> None:
    p = Pipeline.create("p", str(uuid4()))
    s1 = PipelineStep.create(
        str(p.id),
        1,
        "a",
        StepType.SSH_COMMAND,
        "echo",
        OnFailurePolicy.STOP,
    )
    repo = MemoryPipelineRepo(p, [s1])
    use_case = ReorderSteps(repo)
    with pytest.raises(ValidationAppError):
        await use_case.execute(
            ReorderStepsInputDTO(pipeline_id=p.id, ordered_step_ids=[s1.id, uuid4()])
        )
