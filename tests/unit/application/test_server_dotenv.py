"""Testes de leitura / escrita do `.env` remoto (use cases)."""

from uuid import uuid4

import pytest

from src.application import NotFoundAppError, ValidationAppError
from src.application.use_cases.environments.server_dotenv import ReadServerDotenv, WriteServerDotenv
from src.domain.entities.environment import Environment
from src.domain.entities.server import Server
from src.domain.value_objects.environment_type import EnvironmentType
from src.domain.value_objects.server_connection_kind import ServerConnectionKind
from tests.unit.application.fakes import (
    FakeDockerExecService,
    FakeKeyCipher,
    FakeSSHService,
    MemoryEnvironmentRepo,
    MemoryServerRepo,
)


@pytest.mark.asyncio
async def test_read_server_dotenv_when_file_missing() -> None:
    project_id = uuid4()
    server = Server.create(
        "srv",
        "10.0.0.1",
        22,
        "ubuntu",
        "enc:key",
        uuid4(),
        project_directory="/app/repo",
    )
    env = Environment.create(
        str(project_id),
        "staging",
        EnvironmentType.STAGING,
        str(server.id),
        "/var/fallback",
    )
    env_repo = MemoryEnvironmentRepo()
    await env_repo.create(env)
    server_repo = MemoryServerRepo()
    await server_repo.create(server)

    ssh = FakeSSHService(execute_return=(0, "__ENV_MISSING__\n"))
    uc = ReadServerDotenv(
        environment_repo=env_repo,
        server_repo=server_repo,
        key_cipher=FakeKeyCipher(),
        ssh_service=ssh,
        docker_exec=FakeDockerExecService(),
    )
    content, exists, path = await uc.execute(project_id, env.id)
    assert content == ""
    assert exists is False
    assert path == "/app/repo/.env"


@pytest.mark.asyncio
async def test_read_server_dotenv_wrong_project() -> None:
    project_id = uuid4()
    other = uuid4()
    server = Server.create("srv", "10.0.0.1", 22, "ubuntu", "enc:key", uuid4())
    env = Environment.create(
        str(other),
        "staging",
        EnvironmentType.STAGING,
        str(server.id),
        "/app",
    )
    env_repo = MemoryEnvironmentRepo()
    await env_repo.create(env)
    server_repo = MemoryServerRepo()
    await server_repo.create(server)
    uc = ReadServerDotenv(
        environment_repo=env_repo,
        server_repo=server_repo,
        key_cipher=FakeKeyCipher(),
        ssh_service=FakeSSHService(),
        docker_exec=FakeDockerExecService(),
    )
    with pytest.raises(NotFoundAppError):
        await uc.execute(project_id, env.id)


@pytest.mark.asyncio
async def test_write_server_dotenv_too_large() -> None:
    project_id = uuid4()
    server = Server.create(
        "srv",
        "10.0.0.1",
        22,
        "ubuntu",
        "enc:key",
        uuid4(),
        project_directory="/app",
    )
    env = Environment.create(
        str(project_id),
        "staging",
        EnvironmentType.STAGING,
        str(server.id),
        "/var/www",
    )
    env_repo = MemoryEnvironmentRepo()
    await env_repo.create(env)
    server_repo = MemoryServerRepo()
    await server_repo.create(server)
    uc = WriteServerDotenv(
        environment_repo=env_repo,
        server_repo=server_repo,
        key_cipher=FakeKeyCipher(),
        ssh_service=FakeSSHService(),
        docker_exec=FakeDockerExecService(),
    )
    huge = "x" * (256 * 1024 + 1)
    with pytest.raises(ValidationAppError):
        await uc.execute(project_id, env.id, huge)


@pytest.mark.asyncio
async def test_write_server_dotenv_ssh_success() -> None:
    project_id = uuid4()
    server = Server.create(
        "srv",
        "10.0.0.1",
        22,
        "ubuntu",
        "enc:key",
        uuid4(),
        project_directory="/app",
    )
    env = Environment.create(
        str(project_id),
        "staging",
        EnvironmentType.STAGING,
        str(server.id),
        "/var/www",
    )
    env_repo = MemoryEnvironmentRepo()
    await env_repo.create(env)
    server_repo = MemoryServerRepo()
    await server_repo.create(server)
    ssh = FakeSSHService(execute_return=(0, ""))
    uc = WriteServerDotenv(
        environment_repo=env_repo,
        server_repo=server_repo,
        key_cipher=FakeKeyCipher(),
        ssh_service=ssh,
        docker_exec=FakeDockerExecService(),
    )
    path = await uc.execute(project_id, env.id, "KEY=value\n")
    assert path == "/app/.env"
    cmd = str(ssh.last_execute_kwargs.get("command", ""))
    assert "base64" in cmd
    assert ssh.last_execute_kwargs.get("timeout_seconds") == 120


@pytest.mark.asyncio
async def test_read_dotenv_docker_local() -> None:
    project_id = uuid4()
    server = Server.create(
        "dock",
        "localhost",
        22,
        "",
        "enc:k",
        uuid4(),
        connection_kind=ServerConnectionKind.LOCAL_DOCKER,
        docker_container_name="myapp",
        project_directory="/srv",
    )
    env = Environment.create(
        str(project_id),
        "local",
        EnvironmentType.STAGING,
        str(server.id),
        "/unused",
    )
    env_repo = MemoryEnvironmentRepo()
    await env_repo.create(env)
    server_repo = MemoryServerRepo()
    await server_repo.create(server)
    docker = FakeDockerExecService(exec_result=(0, "FOO=bar\n"))
    uc = ReadServerDotenv(
        environment_repo=env_repo,
        server_repo=server_repo,
        key_cipher=FakeKeyCipher(),
        ssh_service=FakeSSHService(),
        docker_exec=docker,
    )
    content, exists, path = await uc.execute(project_id, env.id)
    assert exists is True
    assert "FOO=bar" in content
    assert path == "/srv/.env"
