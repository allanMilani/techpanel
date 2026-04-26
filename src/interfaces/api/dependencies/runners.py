from typing import Annotated

from fastapi import Depends

from src.domain.ports.repositories import (
    IEnvironmentRepository,
    IPipelineRepository,
    IServerRepository,
)
from src.domain.ports.services import INotificationService, IRunnerRegistry
from src.domain.ports.services.i_key_cipher import IKeyCipher
from src.domain.ports.services.i_ssh_service import ISSHService
from src.domain.value_objects.step_type import StepType
from src.infrastructure.runners.http_healthcheck_runner import HttpHealthcheckRunner
from src.infrastructure.runners.notify_webhook_runner import NotifyWebhookRunner
from src.infrastructure.runners.runner_registry import RunnerRegistry
from src.infrastructure.runners.ssh_command_runner import SshCommandRunner
from src.interfaces.api.dependencies.core import (
    get_environment_repository,
    get_pipeline_repository,
    get_server_repository,
)
from src.interfaces.api.dependencies.servers import get_key_cipher, get_ssh_service


class NoopNotificationService(INotificationService):
    async def notify_execution_failed(self, execution, failed_step) -> None:
        _ = execution
        _ = failed_step


def get_notification_service() -> INotificationService:
    return NoopNotificationService()


def get_ssh_command_runner(
    environment_repo: Annotated[
        IEnvironmentRepository, Depends(get_environment_repository)
    ],
    pipeline_repo: Annotated[IPipelineRepository, Depends(get_pipeline_repository)],
    server_repo: Annotated[IServerRepository, Depends(get_server_repository)],
    key_cipher: Annotated[IKeyCipher, Depends(get_key_cipher)],
    ssh_service: Annotated[ISSHService, Depends(get_ssh_service)],
) -> SshCommandRunner:
    return SshCommandRunner(
        environment_repo=environment_repo,
        pipeline_repo=pipeline_repo,
        server_repo=server_repo,
        key_cipher=key_cipher,
        ssh_service=ssh_service,
    )


def get_runner_registry(
    ssh_runner: Annotated[SshCommandRunner, Depends(get_ssh_command_runner)],
) -> IRunnerRegistry:
    return RunnerRegistry(
        runners={
            StepType.SSH_COMMAND: ssh_runner,
            StepType.HTTP_HEALTHCHECK: HttpHealthcheckRunner(),
            StepType.NOTIFY_WEBHOOK: NotifyWebhookRunner(),
        }
    )
