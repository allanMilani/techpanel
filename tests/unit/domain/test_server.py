import pytest

from src.domain.entities.server import Server
from src.domain.errors import ValidationError


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