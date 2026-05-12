from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True, frozen=True)
class CreateServerInputDTO:
    name: str
    host: str
    port: int
    ssh_user: str
    private_key_plain: str
    created_by: UUID
    connection_kind: str = "ssh"
    docker_container_name: str | None = None
    ssh_strict_host_key_checking: bool = False
    project_directory: str | None = None


@dataclass(slots=True, frozen=True)
class ServerOutputDTO:
    id: UUID
    name: str
    host: str
    port: int
    ssh_user: str
    created_by: UUID
    connection_kind: str
    docker_container_name: str | None
    ssh_strict_host_key_checking: bool
    project_directory: str | None = None


@dataclass(slots=True, frozen=True)
class UpdateServerInputDTO:
    name: str
    host: str
    port: int
    ssh_user: str
    private_key_plain: str | None = None
    connection_kind: str = "ssh"
    docker_container_name: str | None = None
    ssh_strict_host_key_checking: bool = False
    project_directory: str | None = None
