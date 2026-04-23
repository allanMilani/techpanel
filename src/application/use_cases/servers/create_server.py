from src.application.dtos import CreateServerInputDTO, ServerOutputDTO
from src.domain.ports.repositories import IServerRepository
from src.domain.entities.server import Server


class CreateServer:
    def __init__(self, server_repo: IServerRepository, key_cipher) -> None:
        self.server_repo = server_repo
        self.key_cipher = key_cipher

    async def execute(self, dto: CreateServerInputDTO) -> ServerOutputDTO:
        encrypted_key = self.key_cipher.encrypt(dto.private_key_plain)

        server = Server.create(
            name=dto.name,
            host=dto.host,
            port=dto.port,
            ssh_user=dto.ssh_user,
            private_key_enc=encrypted_key,
            created_by=dto.created_by,
        )

        server = await self.server_repo.create(server)

        return ServerOutputDTO(
            id=server.id,
            name=server.name,
            host=server.host,
            port=server.port,
            ssh_user=server.ssh_user,
            created_by=server.created_by,
        )
