"""Comportamento de cwd / pipeline_initial_directory no runner SSH."""

from uuid import uuid4

import pytest
from dataclasses import replace

from src.domain.entities.environment import Environment
from src.domain.entities.pipeline import Pipeline
from src.domain.entities.pipeline_step import PipelineStep
from src.domain.entities.server import Server
from src.domain.value_objects.environment_type import EnvironmentType
from src.domain.value_objects.on_failure_policy import OnFailurePolicy
from src.domain.value_objects.server_connection_kind import ServerConnectionKind
from src.domain.value_objects.step_type import StepType
from src.infrastructure.runners.ssh_command_runner import SshCommandRunner
from tests.unit.application.fakes import (
    FakeDockerExecService,
    FakeKeyCipher,
    FakeSSHService,
    MemoryEnvironmentRepo,
    MemoryPipelineRepo,
    MemoryServerRepo,
)


async def _runner_with_repos(
    *,
    env_wd: str,
    step_wd: str | None,
) -> tuple[SshCommandRunner, FakeSSHService, PipelineStep]:
    env_id = uuid4()
    server_id = uuid4()
    pipeline = Pipeline.create("p", str(env_id))
    step = PipelineStep.create(
        str(pipeline.id),
        1,
        "s1",
        StepType.SSH_COMMAND,
        "true",
        OnFailurePolicy.STOP,
        working_directory=step_wd,
    )
    env = Environment.create(
        project_id=str(uuid4()),
        name="stg",
        environment_type=EnvironmentType.STAGING,
        server_id=str(server_id),
        working_directory=env_wd,
    )
    env = replace(env, id=env_id)
    cipher = FakeKeyCipher()
    server = Server.create(
        name="srv",
        host="127.0.0.1",
        port=22,
        ssh_user="u",
        private_key_enc=cipher.encrypt("k"),
        created_by=uuid4(),
    )
    server = replace(server, id=server_id)

    env_repo = MemoryEnvironmentRepo()
    await env_repo.create(env)
    server_repo = MemoryServerRepo()
    await server_repo.create(server)
    pipe_repo = MemoryPipelineRepo(pipeline, [step])
    ssh = FakeSSHService()
    runner = SshCommandRunner(
        environment_repo=env_repo,
        pipeline_repo=pipe_repo,
        server_repo=server_repo,
        key_cipher=cipher,
        ssh_service=ssh,
        docker_exec=FakeDockerExecService(),
    )
    return runner, ssh, step


@pytest.mark.asyncio
async def test_pipeline_session_omits_cwd_when_step_dir_equals_environment() -> None:
    exec_id = uuid4()
    runner, ssh, step = await _runner_with_repos(
        env_wd="/var/www/app",
        step_wd="/var/www/app",
    )
    await runner.run(step, execution_id=exec_id)
    assert ssh.last_execute_kwargs["cwd"] is None
    assert ssh.last_execute_kwargs["pipeline_initial_directory"] == "/var/www/app"


@pytest.mark.asyncio
async def test_pipeline_session_passes_distinct_step_working_directory() -> None:
    exec_id = uuid4()
    runner, ssh, step = await _runner_with_repos(
        env_wd="/var/www/app",
        step_wd="/opt/other",
    )
    await runner.run(step, execution_id=exec_id)
    assert ssh.last_execute_kwargs["cwd"] == "/opt/other"
    assert ssh.last_execute_kwargs["pipeline_initial_directory"] == "/var/www/app"


@pytest.mark.asyncio
async def test_one_shot_does_not_pass_pipeline_initial_directory() -> None:
    runner, ssh, step = await _runner_with_repos(
        env_wd="/var/www/app",
        step_wd=None,
    )
    await runner.run(step, execution_id=None)
    assert ssh.last_execute_kwargs["cwd"] == "/var/www/app"
    assert ssh.last_execute_kwargs["pipeline_initial_directory"] is None


@pytest.mark.asyncio
async def test_docker_pipeline_omits_cwd_when_step_dir_equals_environment() -> None:
    env_id = uuid4()
    server_id = uuid4()
    pipeline = Pipeline.create("p", str(env_id))
    step = PipelineStep.create(
        str(pipeline.id),
        1,
        "s1",
        StepType.SSH_COMMAND,
        "true",
        OnFailurePolicy.STOP,
        working_directory="/var/www/app",
    )
    env = Environment.create(
        project_id=str(uuid4()),
        name="stg",
        environment_type=EnvironmentType.STAGING,
        server_id=str(server_id),
        working_directory="/var/www/app",
    )
    env = replace(env, id=env_id)
    cipher = FakeKeyCipher()
    server = Server.create(
        name="ctn",
        host="local",
        port=22,
        ssh_user="root",
        private_key_enc=cipher.encrypt("unused"),
        created_by=uuid4(),
        connection_kind=ServerConnectionKind.LOCAL_DOCKER,
        docker_container_name="app",
    )
    server = replace(server, id=server_id)
    env_repo = MemoryEnvironmentRepo()
    await env_repo.create(env)
    server_repo = MemoryServerRepo()
    await server_repo.create(server)
    pipe_repo = MemoryPipelineRepo(pipeline, [step])
    ssh = FakeSSHService()
    docker = FakeDockerExecService()
    runner = SshCommandRunner(
        environment_repo=env_repo,
        pipeline_repo=pipe_repo,
        server_repo=server_repo,
        key_cipher=cipher,
        ssh_service=ssh,
        docker_exec=docker,
    )
    exec_id = uuid4()
    await runner.run(step, execution_id=exec_id)
    assert docker.last_execute_kwargs["execution_id"] == exec_id
    assert docker.last_execute_kwargs["pipeline_initial_directory"] == "/var/www/app"
    assert docker.last_execute_kwargs["cwd"] is None


@pytest.mark.asyncio
async def test_docker_one_shot_uses_step_working_directory_not_cwd_for_shell() -> None:
    env_id = uuid4()
    server_id = uuid4()
    pipeline = Pipeline.create("p", str(env_id))
    step = PipelineStep.create(
        str(pipeline.id),
        1,
        "s1",
        StepType.SSH_COMMAND,
        "true",
        OnFailurePolicy.STOP,
        working_directory="/opt/other",
    )
    env = Environment.create(
        project_id=str(uuid4()),
        name="stg",
        environment_type=EnvironmentType.STAGING,
        server_id=str(server_id),
        working_directory="/var/www/app",
    )
    env = replace(env, id=env_id)
    cipher = FakeKeyCipher()
    server = Server.create(
        name="ctn",
        host="local",
        port=22,
        ssh_user="root",
        private_key_enc=cipher.encrypt("unused"),
        created_by=uuid4(),
        connection_kind=ServerConnectionKind.LOCAL_DOCKER,
        docker_container_name="app",
    )
    server = replace(server, id=server_id)
    env_repo = MemoryEnvironmentRepo()
    await env_repo.create(env)
    server_repo = MemoryServerRepo()
    await server_repo.create(server)
    pipe_repo = MemoryPipelineRepo(pipeline, [step])
    docker = FakeDockerExecService()
    runner = SshCommandRunner(
        environment_repo=env_repo,
        pipeline_repo=pipe_repo,
        server_repo=server_repo,
        key_cipher=cipher,
        ssh_service=FakeSSHService(),
        docker_exec=docker,
    )
    await runner.run(step, execution_id=None)
    assert docker.last_execute_kwargs["cwd"] == "/opt/other"
    assert docker.last_execute_kwargs["execution_id"] is None
    assert docker.last_execute_kwargs["pipeline_initial_directory"] is None


@pytest.mark.asyncio
async def test_pipeline_session_uses_server_project_directory_as_initial_cd() -> None:
    env_id = uuid4()
    server_id = uuid4()
    pipeline = Pipeline.create("p", str(env_id))
    step = PipelineStep.create(
        str(pipeline.id),
        1,
        "s1",
        StepType.SSH_COMMAND,
        "true",
        OnFailurePolicy.STOP,
        working_directory="/srv/app",
    )
    env = Environment.create(
        project_id=str(uuid4()),
        name="stg",
        environment_type=EnvironmentType.STAGING,
        server_id=str(server_id),
        working_directory="/var/www/other",
    )
    env = replace(env, id=env_id)
    cipher = FakeKeyCipher()
    server = Server.create(
        name="srv",
        host="127.0.0.1",
        port=22,
        ssh_user="u",
        private_key_enc=cipher.encrypt("k"),
        created_by=uuid4(),
        project_directory="/srv/app",
    )
    server = replace(server, id=server_id)
    env_repo = MemoryEnvironmentRepo()
    await env_repo.create(env)
    server_repo = MemoryServerRepo()
    await server_repo.create(server)
    pipe_repo = MemoryPipelineRepo(pipeline, [step])
    ssh = FakeSSHService()
    runner = SshCommandRunner(
        environment_repo=env_repo,
        pipeline_repo=pipe_repo,
        server_repo=server_repo,
        key_cipher=cipher,
        ssh_service=ssh,
        docker_exec=FakeDockerExecService(),
    )
    exec_id = uuid4()
    await runner.run(step, execution_id=exec_id)
    assert ssh.last_execute_kwargs["cwd"] is None
    assert ssh.last_execute_kwargs["pipeline_initial_directory"] == "/srv/app"


@pytest.mark.asyncio
async def test_docker_one_shot_uses_project_root_when_step_has_no_workdir() -> None:
    env_id = uuid4()
    server_id = uuid4()
    pipeline = Pipeline.create("p", str(env_id))
    step = PipelineStep.create(
        str(pipeline.id),
        1,
        "s1",
        StepType.SSH_COMMAND,
        "true",
        OnFailurePolicy.STOP,
        working_directory=None,
    )
    env = Environment.create(
        project_id=str(uuid4()),
        name="stg",
        environment_type=EnvironmentType.STAGING,
        server_id=str(server_id),
        working_directory="/var/www/app",
    )
    env = replace(env, id=env_id)
    cipher = FakeKeyCipher()
    server = Server.create(
        name="ctn",
        host="local",
        port=22,
        ssh_user="root",
        private_key_enc=cipher.encrypt("unused"),
        created_by=uuid4(),
        connection_kind=ServerConnectionKind.LOCAL_DOCKER,
        docker_container_name="app",
        project_directory="/srv/root",
    )
    server = replace(server, id=server_id)
    env_repo = MemoryEnvironmentRepo()
    await env_repo.create(env)
    server_repo = MemoryServerRepo()
    await server_repo.create(server)
    pipe_repo = MemoryPipelineRepo(pipeline, [step])
    docker = FakeDockerExecService()
    runner = SshCommandRunner(
        environment_repo=env_repo,
        pipeline_repo=pipe_repo,
        server_repo=server_repo,
        key_cipher=cipher,
        ssh_service=FakeSSHService(),
        docker_exec=docker,
    )
    await runner.run(step, execution_id=None)
    assert docker.last_execute_kwargs["cwd"] == "/srv/root"
    assert docker.last_execute_kwargs["execution_id"] is None
    assert docker.last_execute_kwargs["pipeline_initial_directory"] is None
