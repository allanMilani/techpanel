from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from src.application.dtos import CreateServerInputDTO, UpdateServerInputDTO
from src.application.use_cases.servers.check_ssh_connection import CheckSSHConnection
from src.application.use_cases.servers.create_server import CreateServer
from src.application.use_cases.servers.delete_server import DeleteServer
from src.application.use_cases.servers.list_servers import ListServers
from src.application.use_cases.servers.update_server import UpdateServer
from src.domain.ports.repositories import IUserRepository
from src.interfaces.api.dependencies import (
    CurrentUser,
    get_check_ssh_connection_use_case,
    get_create_server_use_case,
    get_delete_server_use_case,
    get_list_servers_use_case,
    get_update_server_use_case,
    require_admin,
)
from src.interfaces.api.dependencies.core import get_user_repository
from src.interfaces.api.dependencies.pagination import Pagination, get_pagination
from src.interfaces.api.schemas import (
    ServerCreateRequest,
    ServerResponse,
    ServerUpdateRequest,
    TestConnectionResponse,
)
from src.interfaces.api.schemas.paged_lists import ServersListPageResponse

router = APIRouter(prefix="/servers", tags=["servers"])


@router.get("/", response_model=ServersListPageResponse, status_code=status.HTTP_200_OK)
async def list_servers(
    _current_user: Annotated[CurrentUser, Depends(require_admin)],
    pagination: Annotated[Pagination, Depends(get_pagination)],
    use_case: Annotated[ListServers, Depends(get_list_servers_use_case)],
) -> ServersListPageResponse:
    out = await use_case.execute(pagination.page, pagination.per_page)
    return ServersListPageResponse(
        items=[
            ServerResponse(
                id=str(server.id),
                name=server.name,
                host=server.host,
                port=server.port,
                ssh_user=server.ssh_user,
                created_by=str(server.created_by),
                connection_kind=server.connection_kind,
                docker_container_name=server.docker_container_name,
                ssh_strict_host_key_checking=server.ssh_strict_host_key_checking,
                project_directory=server.project_directory,
            )
            for server in out.items
        ],
        total=out.total,
        page=out.page,
        per_page=out.per_page,
        total_pages=out.total_pages,
    )


@router.post("/", response_model=ServerResponse, status_code=status.HTTP_201_CREATED)
async def create_server(
    payload: ServerCreateRequest,
    current_user: Annotated[CurrentUser, Depends(require_admin)],
    user_repo: Annotated[IUserRepository, Depends(get_user_repository)],
    use_case: Annotated[CreateServer, Depends(get_create_server_use_case)],
) -> ServerResponse:
    user_id = UUID(current_user.sub)
    if await user_repo.get_by_id(user_id) is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão inválida: conta não encontrada. Volte a iniciar sessão.",
        )
    out = await use_case.execute(
        CreateServerInputDTO(
            name=payload.name,
            host=payload.host,
            port=payload.port,
            ssh_user=payload.ssh_user,
            private_key_plain=payload.private_key_plain,
            created_by=user_id,
            connection_kind=payload.connection_kind,
            docker_container_name=payload.docker_container_name,
            ssh_strict_host_key_checking=payload.ssh_strict_host_key_checking,
            project_directory=payload.project_directory,
        )
    )

    return ServerResponse(
        id=str(out.id),
        name=out.name,
        host=out.host,
        port=out.port,
        ssh_user=out.ssh_user,
        created_by=str(out.created_by),
        connection_kind=out.connection_kind,
        docker_container_name=out.docker_container_name,
        ssh_strict_host_key_checking=out.ssh_strict_host_key_checking,
        project_directory=out.project_directory,
    )


@router.put(
    "/{server_id}", response_model=ServerResponse, status_code=status.HTTP_200_OK
)
async def update_server(
    server_id: UUID,
    payload: ServerUpdateRequest,
    _current_user: Annotated[CurrentUser, Depends(require_admin)],
    use_case: Annotated[UpdateServer, Depends(get_update_server_use_case)],
) -> ServerResponse:
    out = await use_case.execute(
        server_id,
        UpdateServerInputDTO(
            name=payload.name,
            host=payload.host,
            port=payload.port,
            ssh_user=payload.ssh_user,
            private_key_plain=payload.private_key_plain,
            connection_kind=payload.connection_kind,
            docker_container_name=payload.docker_container_name,
            ssh_strict_host_key_checking=payload.ssh_strict_host_key_checking,
            project_directory=payload.project_directory,
        ),
    )

    return ServerResponse(
        id=str(out.id),
        name=out.name,
        host=out.host,
        port=out.port,
        ssh_user=out.ssh_user,
        created_by=str(out.created_by),
        connection_kind=out.connection_kind,
        docker_container_name=out.docker_container_name,
        ssh_strict_host_key_checking=out.ssh_strict_host_key_checking,
        project_directory=out.project_directory,
    )


@router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_server(
    server_id: UUID,
    _current_user: Annotated[CurrentUser, Depends(require_admin)],
    use_case: Annotated[DeleteServer, Depends(get_delete_server_use_case)],
) -> Response:
    await use_case.execute(server_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{server_id}/test",
    response_model=TestConnectionResponse,
    status_code=status.HTTP_200_OK,
)
async def test_connection(
    server_id: UUID,
    _current_user: Annotated[CurrentUser, Depends(require_admin)],
    use_case: Annotated[CheckSSHConnection, Depends(get_check_ssh_connection_use_case)],
) -> TestConnectionResponse:
    ok, err_code, err_detail = await use_case.execute(server_id)
    return TestConnectionResponse(ok=ok, error_code=err_code, error_detail=err_detail)
