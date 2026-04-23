from uuid import uuid4

import pytest

from src.application.dtos import CreateProjectInputDTO, LinkEnvironmentInputDTO
from src.application.use_cases.projects.create_project import CreateProject
from src.application.use_cases.projects.link_environment import LinkEnvironment
from src.domain.entities.server import Server
from src.domain.value_objects.environment_type import EnvironmentType

from tests.unit.application.fakes import (
    MemoryEnvironmentRepo,
    MemoryProjectRepo,
    MemoryServerRepo,
)


@pytest.mark.asyncio
async def test_create_project() -> None:
    repo = MemoryProjectRepo()
    use_case = CreateProject(repo)
    uid = uuid4()
    out = await use_case.execute(
        CreateProjectInputDTO(
            name="TechPanel",
            repo_github="org/techpanel",
            tech_stack="python",
            created_by=uid,
        )
    )
    assert out.name == "TechPanel"
    assert len(await repo.list_all()) == 1


@pytest.mark.asyncio
async def test_link_environment() -> None:
    proj_repo = MemoryProjectRepo()
    srv_repo = MemoryServerRepo()
    env_repo = MemoryEnvironmentRepo()

    from src.domain.entities.project import Project

    uid = uuid4()
    project = Project.create("p", "org/repo", "py", str(uid))
    await proj_repo.create(project)
    server = Server.create(
        name="s",
        host="h",
        port=22,
        ssh_user="u",
        private_key_enc="enc",
        created_by=str(uid),
    )
    await srv_repo.create(server)

    use_case = LinkEnvironment(proj_repo, srv_repo, env_repo)
    env = await use_case.execute(
        LinkEnvironmentInputDTO(
            project_id=project.id,
            name="staging",
            environment_type=EnvironmentType.STAGING.value,
            server_id=server.id,
            working_directory="/var/www",
        )
    )
    assert env.name == "staging"
    assert env.environment_type == EnvironmentType.STAGING
