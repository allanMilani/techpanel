from __future__ import annotations

import shlex

from src.application import NotFoundAppError
from src.application.use_cases.executions.remote_server_shell import run_remote_shell
from src.application.utils.git_ref import is_safe_git_ref
from src.application.utils.workspace_paths import effective_project_root
from src.domain.entities.pipeline import Pipeline
from src.domain.ports.repositories import IEnvironmentRepository, IServerRepository
from src.domain.ports.services import IDockerExecService, IKeyCipher, ISSHService


def build_git_prepare_script(quoted_root: str, quoted_ref: str) -> str:
    """Script bash único: reset/clean, checkout, pull só em branch (não detached)."""
    return (
        "set -euo pipefail\n"
        f"cd {quoted_root}\n"
        "git fetch --all --prune\n"
        "git reset --hard\n"
        "git clean -fd\n"
        f"git checkout {quoted_ref}\n"
        "if git symbolic-ref -q HEAD >/dev/null 2>&1; then\n"
        "  git pull --ff-only || git pull || true\n"
        "fi\n"
    )


class WorkspaceGitPrepare:
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

    async def run(
        self,
        *,
        pipeline: Pipeline,
        branch_or_tag: str,
    ) -> tuple[int, str]:
        env = await self.environment_repo.get_by_id(pipeline.environment_id)
        if env is None:
            raise NotFoundAppError("Environment not found")

        server = await self.server_repo.get_by_id(env.server_id)
        if server is None:
            raise NotFoundAppError("Server not found")

        root = effective_project_root(server, env)
        if not root:
            return (
                1,
                "Diretório do projeto não configurado: defina project_directory no servidor "
                "ou working_directory no ambiente.",
            )

        ref = branch_or_tag.strip()
        if not is_safe_git_ref(ref):
            return 1, "Branch ou tag inválida para sincronização Git."

        quoted_root = shlex.quote(root)
        quoted_ref = shlex.quote(ref)
        script = build_git_prepare_script(quoted_root, quoted_ref)
        inner = shlex.quote(script)
        command = f"bash -lc {inner}"

        return await run_remote_shell(
            server=server,
            command=command,
            key_cipher=self.key_cipher,
            ssh_service=self.ssh_service,
            docker_exec=self.docker_exec,
            timeout_seconds=600,
        )
