from uuid import uuid4

import pytest

from src.application import NotFoundAppError
from src.application.dtos import UpdateServerInputDTO
from src.application.use_cases.servers.delete_server import DeleteServer
from src.application.use_cases.servers.list_servers import ListServers
from src.application.use_cases.servers.update_server import UpdateServer
from src.domain.entities.server import Server
from tests.unit.application.fakes import FakeKeyCipher, MemoryServerRepo


@pytest.mark.asyncio
async def test_list_servers_returns_output_dto_list() -> None:
    repo = MemoryServerRepo()
    uid = uuid4()

    await repo.create(
        Server.create(
            name="srv-1",
            host="10.1.1.1",
            port=22,
            ssh_user="ubuntu",
            private_key_enc="enc:AAA",
            created_by=uid,
        )
    )

    out = await ListServers(repo).execute(page=1, per_page=20)

    assert out.total == 1
    assert len(out.items) == 1
    assert out.items[0].name == "srv-1"


@pytest.mark.asyncio
async def test_update_server_changes_fields_and_keeps_creator() -> None:
    repo = MemoryServerRepo()
    cipher = FakeKeyCipher()
    uid = uuid4()

    existing = await repo.create(
        Server.create(
            name="srv-1",
            host="10.1.1.1",
            port=22,
            ssh_user="ubuntu",
            private_key_enc=cipher.encrypt("OLD_KEY"),
            created_by=uid,
        )
    )

    out = await UpdateServer(repo, cipher).execute(
        server_id=existing.id,
        dto=UpdateServerInputDTO(
            name="srv-1-updated",
            host="10.1.1.2",
            port=2222,
            ssh_user="root",
            private_key_plain="NEW_KEY",
            connection_kind="ssh",
            docker_container_name=None,
        ),
    )

    assert out.name == "srv-1-updated"
    stored = await repo.get_by_id(existing.id)
    assert stored is not None
    assert stored.created_by == uid
    assert stored.private_key_enc.startswith("enc:")


@pytest.mark.asyncio
async def test_update_server_not_found() -> None:
    repo = MemoryServerRepo()
    cipher = FakeKeyCipher()

    with pytest.raises(NotFoundAppError):
        await UpdateServer(repo, cipher).execute(
            server_id=uuid4(),
            dto=UpdateServerInputDTO(
                name="x",
                host="10.0.0.1",
                port=22,
                ssh_user="ubuntu",
                private_key_plain=None,
                connection_kind="ssh",
                docker_container_name=None,
            ),
        )


@pytest.mark.asyncio
async def test_delete_server_success() -> None:
    repo = MemoryServerRepo()
    uid = uuid4()

    server = await repo.create(
        Server.create(
            name="srv-delete",
            host="10.1.1.3",
            port=22,
            ssh_user="ubuntu",
            private_key_enc="enc:KEY",
            created_by=uid,
        )
    )

    await DeleteServer(repo).execute(server.id)

    assert await repo.get_by_id(server.id) is None


@pytest.mark.asyncio
async def test_delete_server_not_found() -> None:
    repo = MemoryServerRepo()

    with pytest.raises(NotFoundAppError):
        await DeleteServer(repo).execute(uuid4())
