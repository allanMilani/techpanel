"""Executa comando shell remoto (SSH ou docker exec) para um `Server`."""

from __future__ import annotations

from src.domain.entities.server import Server
from src.domain.ports.services import IDockerExecService, IKeyCipher, ISSHService
from src.domain.value_objects.server_connection_kind import ServerConnectionKind


async def run_remote_shell(
    *,
    server: Server,
    command: str,
    key_cipher: IKeyCipher,
    ssh_service: ISSHService,
    docker_exec: IDockerExecService,
    timeout_seconds: int = 300,
) -> tuple[int, str]:
    if server.connection_kind == ServerConnectionKind.LOCAL_DOCKER:
        container = (server.docker_container_name or "").strip()
        if not container:
            return 1, "Servidor Docker local sem nome de container."
        user = server.ssh_user.strip() or None
        return await docker_exec.execute(
            container=container,
            username=user,
            command=command,
            cwd=None,
            timeout_seconds=timeout_seconds,
        )
    private_key = key_cipher.decrypt(server.private_key_enc)
    return await ssh_service.execute(
        host=server.host,
        port=server.port,
        username=server.ssh_user,
        private_key=private_key,
        command=command,
        cwd=None,
        strict_host_key_checking=server.ssh_strict_host_key_checking,
        timeout_seconds=timeout_seconds,
    )
