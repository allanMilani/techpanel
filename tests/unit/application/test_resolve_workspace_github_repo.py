from dataclasses import replace
from uuid import uuid4

import pytest

from src.application.use_cases.pipelines.resolve_workspace_github_repo import (
    ResolveWorkspaceGitHubRepository,
)
from src.domain.entities.environment import Environment
from src.domain.entities.pipeline import Pipeline
from src.domain.entities.server import Server
from src.domain.value_objects.environment_type import EnvironmentType
from tests.unit.application.fakes import (
    FakeDockerExecService,
    FakeKeyCipher,
    FakeSSHService,
    MemoryEnvironmentRepo,
    MemoryPipelineRepo,
    MemoryServerRepo,
)


@pytest.mark.asyncio
async def test_resolve_workspace_github_repo_from_git_remote() -> None:
    env_id = uuid4()
    project_id = uuid4()
    pipeline = Pipeline.create("Deploy", str(env_id))
    server = Server.create(
        "s",
        "10.0.0.1",
        22,
        "u",
        "enc:k",
        uuid4(),
        project_directory="/app/repo",
    )
    env = Environment.create(
        str(project_id),
        "stg",
        EnvironmentType.STAGING,
        str(server.id),
        "/fallback",
    )
    env = replace(env, id=env_id)

    pipe_repo = MemoryPipelineRepo(pipeline, [])
    env_repo = MemoryEnvironmentRepo()
    await env_repo.create(env)
    srv_repo = MemoryServerRepo()
    await srv_repo.create(server)

    ssh = FakeSSHService(execute_return=(0, "git@github.com:myorg/the-real-repo.git\n"))
    uc = ResolveWorkspaceGitHubRepository(
        pipeline_repo=pipe_repo,
        environment_repo=env_repo,
        server_repo=srv_repo,
        key_cipher=FakeKeyCipher(),
        ssh_service=ssh,
        docker_exec=FakeDockerExecService(),
    )
    out = await uc.execute(pipeline.id)
    assert out == "myorg/the-real-repo"
