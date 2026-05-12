"""Resolve `owner/repo` no GitHub a partir do clone em `project_directory` / `working_directory`."""

from __future__ import annotations

import shlex
from uuid import UUID

from src.application.use_cases.executions.remote_server_shell import run_remote_shell
from src.application.utils.github_remote import parse_github_owner_repo_from_remote_url
from src.application.utils.workspace_paths import effective_project_root
from src.domain.ports.repositories import IEnvironmentRepository, IPipelineRepository, IServerRepository
from src.domain.ports.services import IDockerExecService, IKeyCipher, ISSHService


class ResolveWorkspaceGitHubRepository:
    """Executa `git remote get-url origin` no diretório efetivo do projeto (SSH / Docker)."""

    def __init__(
        self,
        pipeline_repo: IPipelineRepository,
        environment_repo: IEnvironmentRepository,
        server_repo: IServerRepository,
        key_cipher: IKeyCipher,
        ssh_service: ISSHService,
        docker_exec: IDockerExecService,
    ) -> None:
        self.pipeline_repo = pipeline_repo
        self.environment_repo = environment_repo
        self.server_repo = server_repo
        self.key_cipher = key_cipher
        self.ssh_service = ssh_service
        self.docker_exec = docker_exec

    async def execute(self, pipeline_id: UUID) -> str | None:
        pipeline = await self.pipeline_repo.get_by_id(pipeline_id)
        if pipeline is None:
            return None

        env = await self.environment_repo.get_by_id(pipeline.environment_id)
        if env is None:
            return None

        server = await self.server_repo.get_by_id(env.server_id)
        if server is None:
            return None

        root = effective_project_root(server, env)
        if not root:
            return None

        quoted_root = shlex.quote(root)
        inner = f"cd {quoted_root} && git remote get-url origin"
        cmd = f"bash -lc {shlex.quote(inner)}"
        try:
            code, out = await run_remote_shell(
                server=server,
                command=cmd,
                key_cipher=self.key_cipher,
                ssh_service=self.ssh_service,
                docker_exec=self.docker_exec,
                timeout_seconds=25,
            )
        except Exception:
            return None

        if code != 0:
            return None
        return parse_github_owner_repo_from_remote_url(out or "")
