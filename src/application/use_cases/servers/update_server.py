from uuid import UUID

from src.application import NotFoundAppError
from src.application.dtos import ServerOutputDTO, UpdateServerInputDTO
from src.domain.entities.server import Server
from src.domain.ports.repositories import IServerRepository
from src.domain.ports.services.i_key_cipher import IKeyCipher


class UpdateServer:
    def __init__(self, server_repo: IServerRepository, key_cipher: IKeyCipher) -> None:
        self.server_repo = server_repo
        self.key_cipher = key_cipher

    async def execute(
        self, server_id: UUID, dto: UpdateServerInputDTO
    ) -> ServerOutputDTO:
        existing = await self.server_repo.get_by_id(server_id)
        if existing is None:
            raise NotFoundAppError("Server not found")

        encrypted_key = (
            self.key_cipher.encrypt(dto.private_key_plain)
            if dto.private_key_plain is not None
            else existing.private_key_enc
        )

        updated = Server(
            id=existing.id,
            name=dto.name,
            host=dto.host,
            port=dto.port,
            ssh_user=dto.ssh_user,
            private_key_enc=encrypted_key,
            created_by=existing.created_by,
        )

        persisted = await self.server_repo.update(updated)

        return ServerOutputDTO(
            id=persisted.id,
            name=persisted.name,
            host=persisted.host,
            port=persisted.port,
            ssh_user=persisted.ssh_user,
            created_by=persisted.created_by,
        )
