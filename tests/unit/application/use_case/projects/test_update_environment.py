from uuid import uuid4

import pytest

from src.application import NotFoundAppError
from src.application.dtos import UpdateEnvironmentInputDTO
from src.application.use_cases.projects.update_environment import UpdateEnvironment
from src.domain.entities.environment import Environment
from src.domain.entities.project import Project
from src.domain.entities.server import Server
from src.domain.errors import ValidationError
from src.domain.value_objects.environment_type import EnvironmentType
from tests.unit.application.fakes import (
    MemoryEnvironmentRepo,
    MemoryProjectRepo,
    MemoryServerRepo,
)


@pytest.mark.asyncio
async def test_update_environment_success() -> None:
    project_repo = MemoryProjectRepo()
    server_repo = MemoryServerRepo()
    environment_repo = MemoryEnvironmentRepo()

    project = await project_repo.create(
        Project.create(
            name="app",
            repo_github="https://github.com/org/app",
            tech_stack="python",
            created_by=str(uuid4()),
        )
    )
    server_old = await server_repo.create(
        Server.create(
            name="srv-old",
            host="10.0.0.1",
            ssh_user="deploy",
            port=22,
            private_key_enc="enc1",
            created_by=str(uuid4()),
        )
    )
    server_new = await server_repo.create(
        Server.create(
            name="srv-new",
            host="10.0.0.2",
            ssh_user="deploy",
            port=22,
            private_key_enc="enc2",
            created_by=str(uuid4()),
        )
    )
    environment = await environment_repo.create(
        Environment.create(
            project_id=str(project.id),
            name="staging",
            environment_type=EnvironmentType.STAGING,
            server_id=str(server_old.id),
            working_directory="/var/www/app-staging",
        )
    )

    use_case = UpdateEnvironment(project_repo, server_repo, environment_repo)
    updated = await use_case.execute(
        project.id,
        environment.id,
        UpdateEnvironmentInputDTO(
            name="production",
            environment_type=EnvironmentType.PRODUCTION.value,
            server_id=server_new.id,
            working_directory="/var/www/app-prod",
            is_active=False,
        ),
    )

    assert updated.id == environment.id
    assert updated.name == "production"
    assert updated.environment_type == EnvironmentType.PRODUCTION
    assert updated.server_id == server_new.id
    assert updated.working_directory == "/var/www/app-prod"
    assert updated.is_active is False


@pytest.mark.asyncio
async def test_update_environment_requires_existing_server() -> None:
    project_repo = MemoryProjectRepo()
    server_repo = MemoryServerRepo()
    environment_repo = MemoryEnvironmentRepo()

    project = await project_repo.create(
        Project.create(
            name="app",
            repo_github="https://github.com/org/app",
            tech_stack="python",
            created_by=str(uuid4()),
        )
    )
    server = await server_repo.create(
        Server.create(
            name="srv",
            host="10.0.0.1",
            ssh_user="deploy",
            port=22,
            private_key_enc="enc1",
            created_by=str(uuid4()),
        )
    )
    environment = await environment_repo.create(
        Environment.create(
            project_id=str(project.id),
            name="staging",
            environment_type=EnvironmentType.STAGING,
            server_id=str(server.id),
            working_directory="/var/www/app-staging",
        )
    )

    use_case = UpdateEnvironment(project_repo, server_repo, environment_repo)

    with pytest.raises(NotFoundAppError):
        await use_case.execute(
            project.id,
            environment.id,
            UpdateEnvironmentInputDTO(
                name="production",
                environment_type=EnvironmentType.PRODUCTION.value,
                server_id=uuid4(),
                working_directory="/var/www/app-prod",
                is_active=True,
            ),
        )


@pytest.mark.asyncio
async def test_update_environment_validates_working_directory() -> None:
    project_repo = MemoryProjectRepo()
    server_repo = MemoryServerRepo()
    environment_repo = MemoryEnvironmentRepo()

    project = await project_repo.create(
        Project.create(
            name="app",
            repo_github="https://github.com/org/app",
            tech_stack="python",
            created_by=str(uuid4()),
        )
    )
    server = await server_repo.create(
        Server.create(
            name="srv",
            host="10.0.0.1",
            ssh_user="deploy",
            port=22,
            private_key_enc="enc1",
            created_by=str(uuid4()),
        )
    )
    environment = await environment_repo.create(
        Environment.create(
            project_id=str(project.id),
            name="staging",
            environment_type=EnvironmentType.STAGING,
            server_id=str(server.id),
            working_directory="/var/www/app-staging",
        )
    )

    use_case = UpdateEnvironment(project_repo, server_repo, environment_repo)

    with pytest.raises(ValidationError):
        await use_case.execute(
            project.id,
            environment.id,
            UpdateEnvironmentInputDTO(
                name="production",
                environment_type=EnvironmentType.PRODUCTION.value,
                server_id=server.id,
                working_directory="var/www/app-prod",
                is_active=True,
            ),
        )
