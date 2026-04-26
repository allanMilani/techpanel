from uuid import uuid4
from dataclasses import replace

import pytest

from src.application.dtos import RunNextStepInputDTO, StartExecutionInputDTO
from src.application.use_cases.executions.run_next_step import RunNextStep
from src.application.use_cases.executions.start_execution import StartExecution
from src.domain.entities.environment import Environment
from src.domain.entities.pipeline import Pipeline
from src.domain.entities.pipeline_step import PipelineStep
from src.domain.value_objects.environment_type import EnvironmentType
from src.domain.value_objects.execution_status import ExecutionStatus
from src.domain.value_objects.on_failure_policy import OnFailurePolicy
from src.domain.value_objects.step_execution_status import StepExecutionStatus
from src.domain.value_objects.step_type import StepType
from tests.unit.application.fakes import (
    FakeNotificationService,
    MemoryEnvironmentRepo,
    FakeRunnerRegistry,
    MemoryExecutionRepo,
    MemoryPipelineRepo,
    MemoryStepExecutionRepo,
)


async def _env_repo_for_pipeline(pipeline: Pipeline) -> MemoryEnvironmentRepo:
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
async def test_engine_marks_failed_and_skips_remaining_on_stop_policy() -> None:
    pipeline = Pipeline.create("Deploy", str(uuid4()))
    s1 = PipelineStep.create(
        str(pipeline.id), 1, "build", StepType.SSH_COMMAND, "make build", OnFailurePolicy.STOP
    )
    s2 = PipelineStep.create(
        str(pipeline.id), 2, "deploy", StepType.SSH_COMMAND, "make deploy", OnFailurePolicy.STOP
    )
    p_repo = MemoryPipelineRepo(pipeline, [s1, s2])
    env_repo = await _env_repo_for_pipeline(pipeline)
    e_repo = MemoryExecutionRepo()
    se_repo = MemoryStepExecutionRepo()

    started = await StartExecution(p_repo, env_repo, e_repo, se_repo).execute(
        StartExecutionInputDTO(
            pipeline_id=pipeline.id,
            triggered_by=uuid4(),
            branch_or_tag="main",
        )
    )

    run_uc = RunNextStep(
        execution_repo=e_repo,
        step_execution_repo=se_repo,
        pipeline_repo=p_repo,
        runner_registry=FakeRunnerRegistry(exit_code=1),
        notification_service=None,
    )
    await run_uc.execute(RunNextStepInputDTO(execution_id=started.id))

    final_execution = await e_repo.get_by_id(started.id)
    assert final_execution is not None
    assert final_execution.status == ExecutionStatus.FAILED

    step_execs = await se_repo.list_by_execution(started.id)
    assert step_execs[0].status == StepExecutionStatus.FAILED
    assert step_execs[1].status == StepExecutionStatus.SKIPPED


@pytest.mark.asyncio
async def test_engine_continue_policy_advances_to_next_step() -> None:
    pipeline = Pipeline.create("Deploy", str(uuid4()))
    s1 = PipelineStep.create(
        str(pipeline.id), 1, "health", StepType.HTTP_HEALTHCHECK, "https://x/health", OnFailurePolicy.CONTINUE
    )
    s2 = PipelineStep.create(
        str(pipeline.id), 2, "notify", StepType.NOTIFY_WEBHOOK, "https://x/hook", OnFailurePolicy.STOP
    )
    p_repo = MemoryPipelineRepo(pipeline, [s1, s2])
    env_repo = await _env_repo_for_pipeline(pipeline)
    e_repo = MemoryExecutionRepo()
    se_repo = MemoryStepExecutionRepo()

    started = await StartExecution(p_repo, env_repo, e_repo, se_repo).execute(
        StartExecutionInputDTO(pipeline_id=pipeline.id, triggered_by=uuid4(), branch_or_tag="main")
    )

    run_uc = RunNextStep(
        execution_repo=e_repo,
        step_execution_repo=se_repo,
        pipeline_repo=p_repo,
        runner_registry=FakeRunnerRegistry(exit_code=1),
        notification_service=None,
    )
    await run_uc.execute(RunNextStepInputDTO(execution_id=started.id))

    # Com continue no primeiro passo, o motor deve avançar e tentar os próximos.
    step_execs = await se_repo.list_by_execution(started.id)
    assert len(step_execs) == 2
    assert step_execs[0].status in {StepExecutionStatus.FAILED, StepExecutionStatus.SUCCESS}