from uuid import UUID

from src.application import NotFoundAppError
from src.domain.entities.server import normalize_docker_container_ref
from src.domain.ports.repositories import IServerRepository
from src.domain.ports.services import IDockerExecService, ISSHService
from src.domain.value_objects.server_connection_kind import ServerConnectionKind


class CheckSSHConnection:
    """Testa conectividade SSH ou acesso ao container Docker, conforme o cadastro."""

    def __init__(
        self,
        server_repo: IServerRepository,
        ssh_service: ISSHService,
        key_cipher,
        docker_exec: IDockerExecService,
    ) -> None:
        self.server_repo = server_repo
        self.ssh_service = ssh_service
        self.key_cipher = key_cipher
        self.docker_exec = docker_exec

    async def execute(self, server_id: UUID) -> bool:
        server = await self.server_repo.get_by_id(server_id)
        if server is None:
            raise NotFoundAppError("Server not found")

        if server.connection_kind == ServerConnectionKind.LOCAL_DOCKER:
            name = normalize_docker_container_ref(server.docker_container_name)
            if not name:
                return False
            return await self.docker_exec.test_container(name)

        private_key = self.key_cipher.decrypt(server.private_key_enc)

        return await self.ssh_service.test_connection(
            host=server.host,
            port=server.port,
            username=server.ssh_user,
            private_key=private_key,
        )
