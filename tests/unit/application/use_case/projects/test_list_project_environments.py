from uuid import uuid4

import pytest

from src.application.use_cases.projects.list_project_environments import (
    ListProjectEnvironments,
)
from tests.unit.application.fakes import (
    MemoryEnvironmentRepo,
    MemoryProjectRepo,
    MemoryServerRepo,
)
from src.domain.entities.environment import Environment
from src.domain.entities.project import Project
from src.domain.entities.server import Server
from src.domain.value_objects.environment_type import EnvironmentType


@pytest.mark.asyncio
async def test_list_project_environments_returns_only_that_project() -> None:
    project_repo = MemoryProjectRepo()
    env_repo = MemoryEnvironmentRepo()
    server_repo = MemoryServerRepo()

    p1 = await project_repo.create(
        Project.create(
            name="app-a",
            repo_github="https://github.com/o/app-a",
            tech_stack="python",
            created_by=str(uuid4()),
        )
    )
    p2 = await project_repo.create(
        Project.create(
            name="app-b",
            repo_github="https://github.com/o/app-b",
            tech_stack="go",
            created_by=str(uuid4()),
        )
    )
    srv = await server_repo.create(
        Server.create(
            name="srv1",
            host="10.0.0.1",
            ssh_user="deploy",
            port=22,
            private_key_enc="enc",
            created_by=str(uuid4()),
        )
    )

    e1 = Environment.create(
        project_id=str(p1.id),
        name="staging",
        environment_type=EnvironmentType.STAGING,
        server_id=str(srv.id),
        working_directory="/var/www/a",
    )
    e2 = Environment.create(
        project_id=str(p1.id),
        name="production",
        environment_type=EnvironmentType.PRODUCTION,
        server_id=str(srv.id),
        working_directory="/var/www/a-prod",
    )
    e_other = Environment.create(
        project_id=str(p2.id),
        name="staging",
        environment_type=EnvironmentType.STAGING,
        server_id=str(srv.id),
        working_directory="/var/www/b",
    )
    await env_repo.create(e1)
    await env_repo.create(e2)
    await env_repo.create(e_other)

    uc = ListProjectEnvironments(project_repo, env_repo)
    result = await uc.execute(p1.id, page=1, per_page=20)

    ids = {e.id for e in result.items}
    assert ids == {e1.id, e2.id}
