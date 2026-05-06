import pytest

from src.domain.entities.server import Server
from src.domain.errors import ValidationError
from src.domain.value_objects.server_connection_kind import ServerConnectionKind


def test_should_create_server_successfully() -> None:
    server = Server.create(
        name="srv-prod-01",
        host="192.168.1.10",
        port=22,
        ssh_user="deploy",
        private_key_enc="encrypted-key",
        created_by="00000000-0000-0000-0000-000000000001",
    )
    assert server.port == 22
    assert server.connection_kind == ServerConnectionKind.SSH


def test_should_create_local_docker_server() -> None:
    server = Server.create(
        name="dev",
        host="127.0.0.1",
        port=22,
        ssh_user="",
        private_key_enc="enc:any",
        created_by="00000000-0000-0000-0000-000000000001",
        connection_kind=ServerConnectionKind.LOCAL_DOCKER,
        docker_container_name="app_web_1",
    )
    assert server.docker_container_name == "app_web_1"


def test_should_normalize_leading_slash_in_docker_container_name() -> None:
    server = Server.create(
        name="dev",
        host="127.0.0.1",
        port=22,
        ssh_user="",
        private_key_enc="enc:any",
        created_by="00000000-0000-0000-0000-000000000001",
        connection_kind=ServerConnectionKind.LOCAL_DOCKER,
        docker_container_name=" /app_web_1 ",
    )
    assert server.docker_container_name == "app_web_1"
    assert server.connection_kind == ServerConnectionKind.LOCAL_DOCKER


def test_should_create_local_docker_with_short_container_id() -> None:
    cid = "a1b2c3d4e5f6"  # 12 hex (prefixo de ID)
    server = Server.create(
        name="dev",
        host="127.0.0.1",
        port=22,
        ssh_user="",
        private_key_enc="enc:any",
        created_by="00000000-0000-0000-0000-000000000001",
        connection_kind=ServerConnectionKind.LOCAL_DOCKER,
        docker_container_name=cid,
    )
    assert server.docker_container_name == cid


def test_should_raise_validation_error_if_port_is_invalid() -> None:
    with pytest.raises(ValidationError):
        Server.create(
            name="srv",
            host="127.0.0.1",
            port=0,
            ssh_user="deploy",
            private_key_enc="key",
            created_by="00000000-0000-0000-0000-000000000001",
        )


def test_should_raise_if_local_docker_without_container() -> None:
    with pytest.raises(ValidationError):
        Server.create(
            name="dev",
            host="127.0.0.1",
            port=22,
            ssh_user="",
            private_key_enc="enc:x",
            created_by="00000000-0000-0000-0000-000000000001",
            connection_kind=ServerConnectionKind.LOCAL_DOCKER,
            docker_container_name="",
        )


def test_should_raise_if_local_docker_identifier_invalid() -> None:
    with pytest.raises(ValidationError):
        Server.create(
            name="dev",
            host="127.0.0.1",
            port=22,
            ssh_user="",
            private_key_enc="enc:x",
            created_by="00000000-0000-0000-0000-000000000001",
            connection_kind=ServerConnectionKind.LOCAL_DOCKER,
            docker_container_name="_nome-invalido",
        )
