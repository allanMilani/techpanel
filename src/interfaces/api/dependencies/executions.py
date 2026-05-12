from typing import Annotated

from fastapi import Depends

from src.application.use_cases.executions.cancel_execution import CancelExecution
from src.application.use_cases.executions.get_execution_logs import GetExecutionLogs
from src.application.use_cases.executions.get_history import GetHistory
from src.application.use_cases.executions.run_next_step import RunNextStep
from src.application.use_cases.executions.start_execution import StartExecution
from src.application.use_cases.executions.workspace_git_prepare import WorkspaceGitPrepare
from src.domain.ports.repositories import (
    IEnvironmentRepository,
    IExecutionRepository,
    IPipelineRepository,
    IServerRepository,
    IStepExecutionRepository,
)
from src.domain.ports.services import (
    IDockerExecService,
    INotificationService,
    ISSHService,
)
from src.domain.ports.services.i_key_cipher import IKeyCipher
from src.domain.ports.services.i_runner_registry import IRunnerRegistry
from src.interfaces.api.dependencies.core import (
    get_environment_repository,
    get_execution_repository,
    get_pipeline_repository,
    get_server_repository,
    get_step_execution_repository,
)
from src.interfaces.api.dependencies.runners import (
    get_notification_service,
    get_runner_registry,
)
from src.interfaces.api.dependencies.servers import (
    get_docker_exec_service,
    get_key_cipher,
    get_ssh_service,
)


def get_cancel_execution_use_case(
    execution_repo: Annotated[IExecutionRepository, Depends(get_execution_repository)],
    step_execution_repo: Annotated[
        IStepExecutionRepository, Depends(get_step_execution_repository)
    ],
    ssh_service: Annotated[ISSHService, Depends(get_ssh_service)],
    docker_exec: Annotated[IDockerExecService, Depends(get_docker_exec_service)],
) -> CancelExecution:
    return CancelExecution(
        execution_repo=execution_repo,
        step_execution_repo=step_execution_repo,
        ssh_service=ssh_service,
        docker_exec=docker_exec,
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


def get_get_history_use_case(
    execution_repo: Annotated[IExecutionRepository, Depends(get_execution_repository)],
) -> GetHistory:
    return GetHistory(execution_repo)


def get_get_execution_logs_use_case(
    execution_repo: Annotated[IExecutionRepository, Depends(get_execution_repository)],
    step_execution_repo: Annotated[
        IStepExecutionRepository, Depends(get_step_execution_repository)
    ],
) -> GetExecutionLogs:
    return GetExecutionLogs(
        execution_repo=execution_repo,
        step_execution_repo=step_execution_repo,
    )


def get_workspace_git_prepare(
    environment_repo: Annotated[
        IEnvironmentRepository, Depends(get_environment_repository)
    ],
    server_repo: Annotated[IServerRepository, Depends(get_server_repository)],
    key_cipher: Annotated[IKeyCipher, Depends(get_key_cipher)],
    ssh_service: Annotated[ISSHService, Depends(get_ssh_service)],
    docker_exec: Annotated[IDockerExecService, Depends(get_docker_exec_service)],
) -> WorkspaceGitPrepare:
    return WorkspaceGitPrepare(
        environment_repo=environment_repo,
        server_repo=server_repo,
        key_cipher=key_cipher,
        ssh_service=ssh_service,
        docker_exec=docker_exec,
    )


def get_run_next_step_use_case(
    execution_repo: Annotated[IExecutionRepository, Depends(get_execution_repository)],
    step_execution_repo: Annotated[
        IStepExecutionRepository, Depends(get_step_execution_repository)
    ],
    pipeline_repo: Annotated[IPipelineRepository, Depends(get_pipeline_repository)],
    runner_registry: Annotated[IRunnerRegistry, Depends(get_runner_registry)],
    workspace_git_prepare: Annotated[
        WorkspaceGitPrepare, Depends(get_workspace_git_prepare)
    ],
    ssh_service: Annotated[ISSHService, Depends(get_ssh_service)],
    docker_exec: Annotated[IDockerExecService, Depends(get_docker_exec_service)],
    notification_service: Annotated[
        INotificationService, Depends(get_notification_service)
    ],
) -> RunNextStep:
    return RunNextStep(
        execution_repo=execution_repo,
        step_execution_repo=step_execution_repo,
        pipeline_repo=pipeline_repo,
        runner_registry=runner_registry,
        workspace_git_prepare=workspace_git_prepare,
        ssh_service=ssh_service,
        docker_exec=docker_exec,
        notification_service=notification_service,
    )
