"""Ler / gravar `.env` no servidor do ambiente (SSH ou Docker local)."""

from __future__ import annotations

import base64
import shlex
from uuid import UUID

from src.application import NotFoundAppError, ValidationAppError
from src.application.use_cases.executions.remote_server_shell import run_remote_shell
from src.application.utils.workspace_paths import remote_dotenv_path
from src.domain.ports.repositories import IEnvironmentRepository, IServerRepository
from src.domain.ports.services import IDockerExecService, IKeyCipher, ISSHService

MAX_DOTENV_BYTES = 256 * 1024
_MISSING_SENTINEL = "__ENV_MISSING__"


class ReadServerDotenv:
    def __init__(
        self,
        environment_repo: IEnvironmentRepository,
        server_repo: IServerRepository,
        key_cipher: IKeyCipher,
        ssh_service: ISSHService,
        docker_exec: IDockerExecService,
    ) -> None:
        self.environment_repo = environment_repo
        self.server_repo = server_repo
        self.key_cipher = key_cipher
        self.ssh_service = ssh_service
        self.docker_exec = docker_exec

    async def execute(self, project_id: UUID, environment_id: UUID) -> tuple[str, bool, str]:
        env = await self.environment_repo.get_by_id(environment_id)
        if env is None or env.project_id != project_id:
            raise NotFoundAppError("Ambiente não encontrado")

        server = await self.server_repo.get_by_id(env.server_id)
        if server is None:
            raise NotFoundAppError("Servidor não encontrado")

        path = remote_dotenv_path(server, env)
        if not path:
            raise ValidationAppError(
                "Diretório do projeto não configurado no servidor nem no ambiente."
            )

        pq = shlex.quote(path)
        inner = f"if [ -f {pq} ]; then cat {pq}; else echo {shlex.quote(_MISSING_SENTINEL)}; fi"
        cmd = f"bash -lc {shlex.quote(inner)}"
        code, out = await run_remote_shell(
            server=server,
            command=cmd,
            key_cipher=self.key_cipher,
            ssh_service=self.ssh_service,
            docker_exec=self.docker_exec,
            timeout_seconds=60,
        )
        if code != 0:
            raise ValidationAppError(out or "Falha ao ler o ficheiro remoto.")

        raw = (out or "").strip()
        if raw == _MISSING_SENTINEL:
            return "", False, path
        return out or "", True, path


class WriteServerDotenv:
    def __init__(
        self,
        environment_repo: IEnvironmentRepository,
        server_repo: IServerRepository,
        key_cipher: IKeyCipher,
        ssh_service: ISSHService,
        docker_exec: IDockerExecService,
    ) -> None:
        self.environment_repo = environment_repo
        self.server_repo = server_repo
        self.key_cipher = key_cipher
        self.ssh_service = ssh_service
        self.docker_exec = docker_exec

    async def execute(self, project_id: UUID, environment_id: UUID, content: str) -> str:
        data = content.encode("utf-8")
        if len(data) > MAX_DOTENV_BYTES:
            raise ValidationAppError(
                f"Conteúdo demasiado grande (máximo {MAX_DOTENV_BYTES} bytes)."
            )

        env = await self.environment_repo.get_by_id(environment_id)
        if env is None or env.project_id != project_id:
            raise NotFoundAppError("Ambiente não encontrado")

        server = await self.server_repo.get_by_id(env.server_id)
        if server is None:
            raise NotFoundAppError("Servidor não encontrado")

        path = remote_dotenv_path(server, env)
        if not path:
            raise ValidationAppError(
                "Diretório do projeto não configurado no servidor nem no ambiente."
            )

        b64 = base64.b64encode(data).decode("ascii")
        dir_part = path.rsplit("/", 1)[0]
        dq = shlex.quote(dir_part)
        pq = shlex.quote(path)
        b64q = shlex.quote(b64)
        inner = (
            "set -euo pipefail\n"
            f"parent={dq}\n"
            f"dest={pq}\n"
            "if [ ! -d \"$parent\" ]; then echo 'Diretório pai não existe' >&2; exit 2; fi\n"
            f"tmp=$(mktemp -p \"$parent\")\n"
            f"printf %s {b64q} | base64 -d > \"$tmp\"\n"
            "mv \"$tmp\" \"$dest\"\n"
        )
        cmd = f"bash -lc {shlex.quote(inner)}"
        code, out = await run_remote_shell(
            server=server,
            command=cmd,
            key_cipher=self.key_cipher,
            ssh_service=self.ssh_service,
            docker_exec=self.docker_exec,
            timeout_seconds=120,
        )
        if code != 0:
            raise ValidationAppError(out or "Falha ao gravar o ficheiro remoto.")
        return path
