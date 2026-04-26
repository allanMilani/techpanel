from uuid import uuid4
from dataclasses import replace

import pytest

from src.application import ConflictAppError, NotFoundAppError, ValidationAppError
from src.application.dtos import RunNextStepInputDTO, StartExecutionInputDTO
from src.application.use_cases.executions.get_execution_logs import GetExecutionLogs
from src.application.use_cases.executions.get_history import GetHistory
from src.application.use_cases.executions.run_next_step import RunNextStep
from src.application.use_cases.executions.start_execution import StartExecution
from src.domain.entities.environment import Environment
from src.domain.entities.execution import Execution
from src.domain.entities.pipeline import Pipeline
from src.domain.entities.pipeline_step import PipelineStep
from src.domain.value_objects.environment_type import EnvironmentType
from src.domain.value_objects.execution_status import ExecutionStatus
from src.domain.value_objects.on_failure_policy import OnFailurePolicy
from src.domain.value_objects.step_type import StepType
from tests.unit.application.fakes import (
    FakeNotificationService,
    FakeRunnerRegistry,
    MemoryEnvironmentRepo,
    MemoryExecutionRepo,
    MemoryPipelineRepo,
    MemoryStepExecutionRepo,
)


async def _build_environment_repo_for_pipeline(pipeline: Pipeline) -> MemoryEnvironmentRepo:
    env_repo = MemoryEnvironmentRepo()
    env = Environment.create(
            project_id=str(uuid4()),
            name="staging",
            environment_type=EnvironmentType.STAGING,
            server_id=str(uuid4()),
            working_directory="/var/www/app",
        )
    env = replace(env, id=pipeline.environment_id)
    await env_repo.create(env)
    return env_repo


@pytest.mark.asyncio
async def test_start_execution_creates_step_executions() -> None:
    env_id = uuid4()
    p = Pipeline.create("Deploy", str(env_id))
    s1 = PipelineStep.create(
        str(p.id),
        1,
        "one",
        StepType.SSH_COMMAND,
        "echo",
        OnFailurePolicy.STOP,
    )
    pipe_repo = MemoryPipelineRepo(p, [s1])
    exec_repo = MemoryExecutionRepo()
    step_repo = MemoryStepExecutionRepo()
    env_repo = await _build_environment_repo_for_pipeline(p)

    use_case = StartExecution(pipe_repo, env_repo, exec_repo, step_repo)
    uid = uuid4()
    out = await use_case.execute(
        StartExecutionInputDTO(
            pipeline_id=p.id,
            triggered_by=uid,
            branch_or_tag="main",
            triggered_by_ip="127.0.0.1",
        )
    )
    assert out.status == "pending"
    rows = await step_repo.list_by_execution(out.id)
    assert len(rows) == 1
    assert rows[0].pipeline_step_id == s1.id


@pytest.mark.asyncio
async def test_start_execution_conflict_when_active_in_environment() -> None:
    env_id = uuid4()
    p = Pipeline.create("Deploy", str(env_id))
    pipe_repo = MemoryPipelineRepo(p, [])
    exec_repo = MemoryExecutionRepo()
    step_repo = MemoryStepExecutionRepo()
    env_repo = await _build_environment_repo_for_pipeline(p)

    active = Execution.create(str(p.id), str(uuid4()), "main").mark_running()
    await exec_repo.create(active)
    exec_repo.set_active_for_env(env_id, active)

    use_case = StartExecution(pipe_repo, env_repo, exec_repo, step_repo)
    with pytest.raises(ConflictAppError):
        await use_case.execute(
            StartExecutionInputDTO(
                pipeline_id=p.id,
                triggered_by=uuid4(),
                branch_or_tag="main",
            )
        )


@pytest.mark.asyncio
async def test_run_next_step_single_successful_step() -> None:
    env_id = uuid4()
    p = Pipeline.create("Deploy", str(env_id))
    s1 = PipelineStep.create(
        str(p.id),
        1,
        "one",
        StepType.SSH_COMMAND,
        "echo",
        OnFailurePolicy.STOP,
    )
    pipe_repo = MemoryPipelineRepo(p, [s1])
    exec_repo = MemoryExecutionRepo()
    step_repo = MemoryStepExecutionRepo()
    env_repo = await _build_environment_repo_for_pipeline(p)

    start = StartExecution(pipe_repo, env_repo, exec_repo, step_repo)
    uid = uuid4()
    started = await start.execute(
        StartExecutionInputDTO(pipeline_id=p.id, triggered_by=uid, branch_or_tag="main")
    )

    run = RunNextStep(exec_repo, step_repo, pipe_repo, FakeRunnerRegistry(0))
    await run.execute(RunNextStepInputDTO(execution_id=started.id))

    final = await exec_repo.get_by_id(started.id)
    assert final is not None
    assert final.status == ExecutionStatus.SUCCESS
    step_execs = await step_repo.list_by_execution(started.id)
    assert step_execs[0].started_at is not None
    assert step_execs[0].finished_at is not None


@pytest.mark.asyncio
async def test_run_next_step_notify_and_stop_requires_service() -> None:
    env_id = uuid4()
    p = Pipeline.create("Deploy", str(env_id))
    s1 = PipelineStep.create(
        str(p.id),
        1,
        "one",
        StepType.SSH_COMMAND,
        "echo",
        OnFailurePolicy.NOTIFY_AND_STOP,
    )
    pipe_repo = MemoryPipelineRepo(p, [s1])
    exec_repo = MemoryExecutionRepo()
    step_repo = MemoryStepExecutionRepo()
    env_repo = await _build_environment_repo_for_pipeline(p)

    start = StartExecution(pipe_repo, env_repo, exec_repo, step_repo)
    started = await start.execute(
        StartExecutionInputDTO(
            pipeline_id=p.id, triggered_by=uuid4(), branch_or_tag="main"
        )
    )

    run = RunNextStep(
        exec_repo,
        step_repo,
        pipe_repo,
        FakeRunnerRegistry(exit_code=1),
        notification_service=None,
    )
    with pytest.raises(ValidationAppError):
        await run.execute(RunNextStepInputDTO(execution_id=started.id))


@pytest.mark.asyncio
async def test_run_next_step_notify_and_stop_with_service() -> None:
    env_id = uuid4()
    p = Pipeline.create("Deploy", str(env_id))
    s1 = PipelineStep.create(
        str(p.id),
        1,
        "one",
        StepType.SSH_COMMAND,
        "echo",
        OnFailurePolicy.NOTIFY_AND_STOP,
    )
    pipe_repo = MemoryPipelineRepo(p, [s1])
    exec_repo = MemoryExecutionRepo()
    step_repo = MemoryStepExecutionRepo()
    env_repo = await _build_environment_repo_for_pipeline(p)
    notifier = FakeNotificationService()

    started = await StartExecution(pipe_repo, env_repo, exec_repo, step_repo).execute(
        StartExecutionInputDTO(
            pipeline_id=p.id, triggered_by=uuid4(), branch_or_tag="main"
        )
    )

    run = RunNextStep(
        exec_repo,
        step_repo,
        pipe_repo,
        FakeRunnerRegistry(exit_code=1),
        notification_service=notifier,
    )
    await run.execute(RunNextStepInputDTO(execution_id=started.id))

    assert len(notifier.calls) == 1
    final = await exec_repo.get_by_id(started.id)
    assert final is not None
    assert final.status == ExecutionStatus.FAILED
    step_execs = await step_repo.list_by_execution(started.id)
    assert step_execs[0].started_at is not None
    assert step_execs[0].finished_at is not None


@pytest.mark.asyncio
async def test_get_execution_logs_maps_dtos() -> None:
    env_id = uuid4()
    p = Pipeline.create("Deploy", str(env_id))
    s1 = PipelineStep.create(
        str(p.id),
        1,
        "one",
        StepType.SSH_COMMAND,
        "echo",
        OnFailurePolicy.STOP,
    )
    pipe_repo = MemoryPipelineRepo(p, [s1])
    exec_repo = MemoryExecutionRepo()
    step_repo = MemoryStepExecutionRepo()
    env_repo = await _build_environment_repo_for_pipeline(p)
    started = await StartExecution(pipe_repo, env_repo, exec_repo, step_repo).execute(
        StartExecutionInputDTO(
            pipeline_id=p.id, triggered_by=uuid4(), branch_or_tag="main"
        )
    )

    logs = GetExecutionLogs(exec_repo, step_repo)
    out = await logs.execute(started.id)
    assert len(out) == 1
    assert out[0].status == "pending"


@pytest.mark.asyncio
async def test_get_history_maps_dtos() -> None:
    env_id = uuid4()
    p = Pipeline.create("Deploy", str(env_id))
    pipe_repo = MemoryPipelineRepo(p, [])
    exec_repo = MemoryExecutionRepo()
    step_repo = MemoryStepExecutionRepo()
    env_repo = await _build_environment_repo_for_pipeline(p)
    started = await StartExecution(pipe_repo, env_repo, exec_repo, step_repo).execute(
        StartExecutionInputDTO(
            pipeline_id=p.id, triggered_by=uuid4(), branch_or_tag="main"
        )
    )

    hist = GetHistory(exec_repo)
    out = await hist.execute(p.id)
    assert len(out) == 1
    assert out[0].id == started.id


@pytest.mark.asyncio
async def test_get_execution_logs_not_found() -> None:
    exec_repo = MemoryExecutionRepo()
    step_repo = MemoryStepExecutionRepo()
    logs = GetExecutionLogs(exec_repo, step_repo)
    with pytest.raises(NotFoundAppError):
        await logs.execute(uuid4())
