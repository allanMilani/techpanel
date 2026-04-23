from typing import Annotated

from fastapi import Depends

from src.application.use_cases.servers.check_ssh_connection import CheckSSHConnection
from src.application.use_cases.servers.create_server import CreateServer
from src.application.use_cases.servers.delete_server import DeleteServer
from src.application.use_cases.servers.list_servers import ListServers
from src.application.use_cases.servers.update_server import UpdateServer
from src.domain.ports.repositories import IServerRepository
from src.domain.ports.services import IKeyCipher, ISSHService
from src.infrastructure.config.settings import get_settings
from src.infrastructure.security.fernet_key_cipher import FernetKeyCipher
from src.infrastructure.services.paramiko_ssh_service import ParamikoSSHService
from src.interfaces.api.dependencies.core import get_server_repository


def get_key_cipher() -> IKeyCipher:
    settings = get_settings()
    return FernetKeyCipher(settings.fernet_key)


def get_ssh_service() -> ISSHService:
    return ParamikoSSHService()


def get_create_server_use_case(
    server_repo: Annotated[IServerRepository, Depends(get_server_repository)],
    key_cipher: Annotated[IKeyCipher, Depends(get_key_cipher)],
) -> CreateServer:
    return CreateServer(server_repo=server_repo, key_cipher=key_cipher)


def get_list_servers_use_case(
    server_repo: Annotated[IServerRepository, Depends(get_server_repository)],
) -> ListServers:
    return ListServers(server_repo=server_repo)


def get_update_server_use_case(
    server_repo: Annotated[IServerRepository, Depends(get_server_repository)],
    key_cipher: Annotated[IKeyCipher, Depends(get_key_cipher)],
) -> UpdateServer:
    return UpdateServer(server_repo=server_repo, key_cipher=key_cipher)


def get_delete_server_use_case(
    server_repo: Annotated[IServerRepository, Depends(get_server_repository)],
) -> DeleteServer:
    return DeleteServer(server_repo=server_repo)


def get_check_ssh_connection_use_case(
    server_repo: Annotated[IServerRepository, Depends(get_server_repository)],
    ssh_service: Annotated[ISSHService, Depends(get_ssh_service)],
    key_cipher: Annotated[IKeyCipher, Depends(get_key_cipher)],
) -> CheckSSHConnection:
    return CheckSSHConnection(
        server_repo=server_repo,
        ssh_service=ssh_service,
        key_cipher=key_cipher,
    )
