from uuid import UUID

from src.application import NotFoundAppError
from src.domain.ports.repositories import IServerRepository


class DeleteServer:
    def __init__(
        self,
        server_repo: IServerRepository,
    ) -> None:
        self.server_repo = server_repo

    async def execute(self, server_id: UUID) -> None:
        existing = await self.server_repo.get_by_id(server_id)
        if existing is None:
            raise NotFoundAppError("Server not found")

        await self.server_repo.delete(server_id)
