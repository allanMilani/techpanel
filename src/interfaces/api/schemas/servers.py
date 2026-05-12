from typing import Literal

from pydantic import BaseModel


class ServerCreateRequest(BaseModel):
    name: str
    host: str
    port: int
    ssh_user: str
    private_key_plain: str = ""
    connection_kind: Literal["ssh", "local_docker"] = "ssh"
    docker_container_name: str | None = None
    ssh_strict_host_key_checking: bool = False
    project_directory: str | None = None


class ServerUpdateRequest(BaseModel):
    name: str
    host: str
    port: int
    ssh_user: str
    private_key_plain: str | None = None
    connection_kind: Literal["ssh", "local_docker"] = "ssh"
    docker_container_name: str | None = None
    ssh_strict_host_key_checking: bool = False
    project_directory: str | None = None


class ServerResponse(BaseModel):
    id: str
    name: str
    host: str
    port: int
    ssh_user: str
    created_by: str
    connection_kind: str
    docker_container_name: str | None = None
    ssh_strict_host_key_checking: bool = False
    project_directory: str | None = None


class TestConnectionResponse(BaseModel):
    ok: bool
    error_code: str | None = None
    error_detail: str | None = None
