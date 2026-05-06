from __future__ import annotations

import asyncio
from src.domain.entities.server import (
    is_valid_docker_container_ref,
    normalize_docker_container_ref,
)
from src.domain.ports.services.i_docker_exec_service import IDockerExecService


def assert_safe_container_name(container: str) -> None:
    if not is_valid_docker_container_ref(normalize_docker_container_ref(container)):
        raise ValueError("Identificador do container Docker inválido.")


class DockerCliExecService(IDockerExecService):
    """Implementação usando o binário `docker` do PATH (CLI)."""

    async def test_container(self, container: str) -> bool:
        """Confere se o container aceita `docker exec` como nas execuções de pipeline."""
        name = normalize_docker_container_ref(container)
        if not name or not is_valid_docker_container_ref(name):
            return False
        try:
            proc = await asyncio.create_subprocess_exec(
                "docker",
                "exec",
                name,
                "sh",
                "-c",
                "true",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
        except FileNotFoundError:
            return False
        try:
            await asyncio.wait_for(proc.wait(), timeout=15)
        except TimeoutError:
            proc.kill()
            return False
        return proc.returncode == 0

    async def execute(
        self,
        container: str,
        username: str | None,
        command: str,
        cwd: str | None,
        timeout_seconds: int,
    ) -> tuple[int, str]:
        name = normalize_docker_container_ref(container)
        try:
            assert_safe_container_name(name)
        except ValueError as e:
            return 1, str(e)
        args: list[str] = ["docker", "exec", "-i"]
        if cwd and cwd.strip():
            args.extend(["-w", cwd.strip()])
        if username and username.strip():
            args.extend(["-u", username.strip()])
        args.extend([name, "sh", "-c", command])
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        try:
            out, _ = await asyncio.wait_for(
                proc.communicate(),
                timeout=max(1, timeout_seconds),
            )
        except TimeoutError:
            proc.kill()
            await proc.wait()
            return 124, "Timeout ao executar docker exec."
        raw = (out or b"").decode("utf-8", errors="replace").strip()
        code = proc.returncode if proc.returncode is not None else 1
        return code, raw
