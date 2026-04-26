from typing import Annotated

from fastapi import Depends

from src.application.use_cases.executions.start_execution import StartExecution
from src.domain.ports.repositories import (
    IEnvironmentRepository,
    IExecutionRepository,
    IPipelineRepository,
    IStepExecutionRepository,
)
from src.interfaces.api.dependencies.core import (
    get_environment_repository,
    get_execution_repository,
    get_pipeline_repository,
    get_step_execution_repository,
)
from src.application.use_cases.executions.run_next_step import RunNextStep
from src.domain.ports.services import INotificationService
from src.domain.ports.services.i_runner_registry import IRunnerRegistry
from src.interfaces.api.dependencies.runners import (
    get_runner_registry,
    get_notification_service,
)


def get_start_execution_use_case(
    pipeline_repo: Annotated[IPipelineRepository, Depends(get_pipeline_repository)],
    environment_repo: Annotated[
        IEnvironmentRepository, Depends(get_environment_repository)
    ],
    execution_repo: Annotated[IExecutionRepository, Depends(get_execution_repository)],
    step_execution_repo: Annotated[
        IStepExecutionRepository, Depends(get_step_execution_repository)
    ],
) -> StartExecution:
    return StartExecution(
        pipeline_repo=pipeline_repo,
        environment_repo=environment_repo,
        execution_repo=execution_repo,
        step_execution_repo=step_execution_repo,
    )


def get_run_next_step_use_case(
    execution_repo: Annotated[IExecutionRepository, Depends(get_execution_repository)],
    step_execution_repo: Annotated[
        IStepExecutionRepository, Depends(get_step_execution_repository)
    ],
    pipeline_repo: Annotated[IPipelineRepository, Depends(get_pipeline_repository)],
    runner_registry: Annotated[IRunnerRegistry, Depends(get_runner_registry)],
    notification_service: Annotated[
        INotificationService, Depends(get_notification_service)
    ],
) -> RunNextStep:
    return RunNextStep(
        execution_repo=execution_repo,
        step_execution_repo=step_execution_repo,
        pipeline_repo=pipeline_repo,
        runner_registry=runner_registry,
        notification_service=notification_service,
    )
