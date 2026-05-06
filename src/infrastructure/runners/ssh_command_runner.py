from src.application import NotFoundAppError
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

    async def run(self, step: PipelineStep) -> tuple[int, str]:
        pipeline = await self.pipeline_repo.get_by_id(step.pipeline_id)
        if pipeline is None:
            raise NotFoundAppError("Pipeline not found")

        environment = await self.environment_repo.get_by_id(pipeline.environment_id)
        if environment is None:
            raise NotFoundAppError("Environment not found")

        server = await self.server_repo.get_by_id(environment.server_id)
        if server is None:
            raise NotFoundAppError("Server not found")

        if server.connection_kind == ServerConnectionKind.LOCAL_DOCKER:
            container = (server.docker_container_name or "").strip()
            if not container:
                return 1, "Servidor Docker local sem nome de container."
            user = server.ssh_user.strip() or None
            return await self.docker_exec.execute(
                container=container,
                username=user,
                command=step.command,
                cwd=step.working_directory,
                timeout_seconds=step.timeout_seconds,
            )

        private_key = self.key_cipher.decrypt(server.private_key_enc)
        return await self.ssh_service.execute(
            host=server.host,
            port=server.port,
            username=server.ssh_user,
            private_key=private_key,
            command=step.command,
            cwd=step.working_directory,
        )
