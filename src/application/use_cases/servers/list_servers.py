from src.application.dtos import ServerOutputDTO
from src.domain.ports.repositories import IServerRepository


class ListServers:
    def __init__(
        self,
        server_repo: IServerRepository,
    ) -> None:
        self.server_repo = server_repo

    async def execute(self) -> list[ServerOutputDTO]:
        servers = await self.server_repo.list_all()
        return [
            ServerOutputDTO(
                id=server.id,
                name=server.name,
                host=server.host,
                port=server.port,
                ssh_user=server.ssh_user,
                created_by=server.created_by,
            )
            for server in servers
        ]
