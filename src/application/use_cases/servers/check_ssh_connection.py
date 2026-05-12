import logging
from uuid import UUID

from src.application import NotFoundAppError
from src.domain.entities.server import normalize_docker_container_ref
from src.domain.ports.repositories import IServerRepository
from src.domain.ports.services import IDockerExecService, ISSHService
from src.domain.value_objects.server_connection_kind import ServerConnectionKind

logger = logging.getLogger(__name__)


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

    async def execute(self, server_id: UUID) -> tuple[bool, str | None, str | None]:
        server = await self.server_repo.get_by_id(server_id)
        if server is None:
            raise NotFoundAppError("Server not found")

        if server.connection_kind == ServerConnectionKind.LOCAL_DOCKER:
            name = normalize_docker_container_ref(server.docker_container_name)
            if not name:
                logger.warning(
                    "server_connection_test_failed server_id=%s kind=local_docker "
                    "error_code=DOCKER_CONTAINER_MISSING",
                    server_id,
                )
                return (
                    False,
                    "DOCKER_CONTAINER_MISSING",
                    "Identificador do container em falta.",
                )
            ok = await self.docker_exec.test_container(name)
            if not ok:
                logger.warning(
                    "server_connection_test_failed server_id=%s kind=local_docker "
                    "container=%s error_code=DOCKER_EXEC_FAILED",
                    server_id,
                    name,
                )
                return (
                    False,
                    "DOCKER_EXEC_FAILED",
                    "Não foi possível aceder ao container.",
                )
            return True, None, None

        private_key = self.key_cipher.decrypt(server.private_key_enc)

        ok, err_code, err_detail = await self.ssh_service.test_connection(
            host=server.host,
            port=server.port,
            username=server.ssh_user,
            private_key=private_key,
            strict_host_key_checking=server.ssh_strict_host_key_checking,
        )
        if not ok:
            logger.warning(
                "server_connection_test_failed server_id=%s kind=ssh host=%s port=%s user=%s "
                "strict_host_keys=%s error_code=%s detail=%s",
                server_id,
                server.host,
                server.port,
                server.ssh_user,
                server.ssh_strict_host_key_checking,
                err_code,
                err_detail,
            )
        return ok, err_code, err_detail
