from uuid import UUID

from src.application import NotFoundAppError
from src.domain.ports.repositories import IServerRepository
from src.domain.ports.services import ISSHService


class CheckSSHConnection:
    """Testa conectividade SSH com credenciais do servidor cadastrado."""

    def __init__(
        self,
        server_repo: IServerRepository,
        ssh_service: ISSHService,
        key_cipher,
    ) -> None:
        self.server_repo = server_repo
        self.ssh_service = ssh_service
        self.key_cipher = key_cipher

    async def execute(self, server_id: UUID) -> bool:
        server = await self.server_repo.get_by_id(server_id)
        if server is None:
            raise NotFoundAppError("Server not found")

        private_key = self.key_cipher.decrypt(server.private_key_enc)

        return await self.ssh_service.test_connection(
            host=server.host,
            port=server.port,
            username=server.ssh_user,
            private_key=private_key,
        )
