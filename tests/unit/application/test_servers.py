from uuid import uuid4

import pytest

from src.application import NotFoundAppError
from src.application.dtos import CreateServerInputDTO
from src.application.use_cases.servers.check_ssh_connection import CheckSSHConnection
from src.application.use_cases.servers.create_server import CreateServer
from src.domain.entities.server import Server

from tests.unit.application.fakes import FakeKeyCipher, FakeSSHService, MemoryServerRepo


@pytest.mark.asyncio
async def test_create_server_encrypts_key() -> None:
    repo = MemoryServerRepo()
    cipher = FakeKeyCipher()
    use_case = CreateServer(repo, cipher)
    uid = uuid4()
    out = await use_case.execute(
        CreateServerInputDTO(
            name="srv",
            host="127.0.0.1",
            port=22,
            ssh_user="deploy",
            private_key_plain="PRIVATE",
            created_by=uid,
        )
    )
    assert out.name == "srv"
    stored = await repo.get_by_id(out.id)
    assert stored is not None
    assert stored.private_key_enc.startswith("enc:")


@pytest.mark.asyncio
async def test_check_ssh_connection_success() -> None:
    repo = MemoryServerRepo()
    cipher = FakeKeyCipher()
    server = Server.create(
        name="srv",
        host="127.0.0.1",
        port=22,
        ssh_user="u",
        private_key_enc=cipher.encrypt("KEY"),
        created_by=str(uuid4()),
    )
    await repo.create(server)

    use_case = CheckSSHConnection(repo, FakeSSHService(result=True), cipher)
    ok = await use_case.execute(server.id)
    assert ok is True


@pytest.mark.asyncio
async def test_check_ssh_connection_not_found() -> None:
    repo = MemoryServerRepo()
    use_case = CheckSSHConnection(repo, FakeSSHService(), FakeKeyCipher())
    with pytest.raises(NotFoundAppError):
        await use_case.execute(uuid4())
