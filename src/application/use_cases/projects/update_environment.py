from dataclasses import replace
from uuid import UUID
from src.application import NotFoundAppError
from src.application.dtos import UpdateEnvironmentInputDTO
from src.domain.entities.environment import Environment
from src.domain.errors import ValidationError
from src.domain.ports.repositories import (
    IEnvironmentRepository,
    IProjectRepository,
    IServerRepository,
)
from src.domain.value_objects.environment_type import EnvironmentType


class UpdateEnvironment:
    def __init__(
        self,
        project_repo: IProjectRepository,
        server_repo: IServerRepository,
        environment_repo: IEnvironmentRepository,
    ) -> None:
        self.project_repo = project_repo
        self.server_repo = server_repo
        self.environment_repo = environment_repo

    async def execute(
        self,
        project_id: UUID,
        environment_id: UUID,
        dto: UpdateEnvironmentInputDTO,
    ) -> Environment:
        project = await self.project_repo.get_by_id(project_id)
        if project is None:
            raise NotFoundAppError("Project not found")

        env = await self.environment_repo.get_by_id(environment_id)
        if env is None or env.project_id != project_id:
            raise NotFoundAppError("Environment not found")

        server = await self.server_repo.get_by_id(dto.server_id)
        if server is None:
            raise NotFoundAppError("Server not found")

        wd = dto.working_directory.strip()
        if not wd.startswith("/"):
            raise ValidationError("Working directory must start with a slash")

        updated = replace(
            env,
            name=dto.name.strip().lower(),
            environment_type=EnvironmentType(dto.environment_type),
            server_id=server.id,
            working_directory=wd,
            is_active=dto.is_active,
        )

        return await self.environment_repo.update(updated)
