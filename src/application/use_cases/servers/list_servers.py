from src.application.dtos import ServerOutputDTO
from src.application.dtos.pagination_dto import PaginatedResult, offset_for_page
from src.domain.ports.repositories import IServerRepository


class ListServers:
    def __init__(
        self,
        server_repo: IServerRepository,
    ) -> None:
        self.server_repo = server_repo

    async def execute(self, page: int, per_page: int) -> PaginatedResult[ServerOutputDTO]:
        offset = offset_for_page(page, per_page)
        servers, total = await self.server_repo.list_all_page(per_page, offset)
        items = [
            ServerOutputDTO(
                id=server.id,
                name=server.name,
                host=server.host,
                port=server.port,
                ssh_user=server.ssh_user,
                created_by=server.created_by,
                connection_kind=server.connection_kind.value,
                docker_container_name=server.docker_container_name,
                ssh_strict_host_key_checking=server.ssh_strict_host_key_checking,
                project_directory=server.project_directory,
            )
            for server in servers
        ]
        return PaginatedResult(
            items=items, total=total, page=page, per_page=per_page
        )
