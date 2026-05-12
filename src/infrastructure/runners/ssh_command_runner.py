from uuid import UUID

from src.application import NotFoundAppError
from src.application.utils.workspace_paths import effective_project_root

from src.domain.entities.pipeline_step import PipelineStep
from src.domain.ports.repositories import (
    IEnvironmentRepository,
    IPipelineRepository,
    IServerRepository,
)
from src.domain.ports.services import IDockerExecService, IKeyCipher, ISSHService
from src.domain.ports.services.i_step_runner import IStepRunner
from src.domain.value_objects.server_connection_kind import ServerConnectionKind


class SshCommandRunner(IStepRunner):
    def __init__(
        self,
        environment_repo: IEnvironmentRepository,
        pipeline_repo: IPipelineRepository,
        server_repo: IServerRepository,
        key_cipher: IKeyCipher,
        ssh_service: ISSHService,
        docker_exec: IDockerExecService,
    ) -> None:
        self.environment_repo = environment_repo
        self.pipeline_repo = pipeline_repo
        self.server_repo = server_repo
        self.key_cipher = key_cipher
        self.ssh_service = ssh_service
        self.docker_exec = docker_exec

    async def run(
        self, step: PipelineStep, *, execution_id: UUID | None = None
    ) -> tuple[int, str]:
        pipeline = await self.pipeline_repo.get_by_id(step.pipeline_id)
        if pipeline is None:
            raise NotFoundAppError("Pipeline not found")

        environment = await self.environment_repo.get_by_id(pipeline.environment_id)
        if environment is None:
            raise NotFoundAppError("Environment not found")

        server = await self.server_repo.get_by_id(environment.server_id)
        if server is None:
            raise NotFoundAppError("Server not found")

        pipeline_base = effective_project_root(server, environment)
        if pipeline_base is not None:
            pipeline_base = pipeline_base.strip() or None

        step_wd = (step.working_directory or "").strip() or None
        cwd_for_shell = step_wd
        if (
            execution_id is not None
            and step_wd is not None
            and pipeline_base is not None
            and step_wd == pipeline_base
        ):
            # Sessão já faz cd a `pipeline_base` ao abrir; repetir o mesmo cd por passo
            # anularia um cd feito no comando do passo anterior.
            cwd_for_shell = None

        pipeline_initial = pipeline_base if execution_id is not None else None

        if server.connection_kind == ServerConnectionKind.LOCAL_DOCKER:
            container = (server.docker_container_name or "").strip()
            if not container:
                return 1, "Servidor Docker local sem nome de container."
            user = server.ssh_user.strip() or None
            docker_cwd = (
                cwd_for_shell
                if execution_id is not None
                else (step.working_directory or pipeline_base)
            )
            return await self.docker_exec.execute(
                container=container,
                username=user,
                command=step.command,
                cwd=docker_cwd,
                timeout_seconds=step.timeout_seconds,
                execution_id=execution_id,
                pipeline_initial_directory=pipeline_initial,
            )

        private_key = self.key_cipher.decrypt(server.private_key_enc)
        ssh_cwd = cwd_for_shell
        if execution_id is None:
            ssh_cwd = step_wd if step_wd else pipeline_base

        return await self.ssh_service.execute(
            host=server.host,
            port=server.port,
            username=server.ssh_user,
            private_key=private_key,
            command=step.command,
            cwd=ssh_cwd,
            strict_host_key_checking=server.ssh_strict_host_key_checking,
            timeout_seconds=step.timeout_seconds,
            execution_id=execution_id,
            pipeline_initial_directory=pipeline_initial,
        )
