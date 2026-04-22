from src.application import NotFoundAppError
from src.application.dtos import LinkEnvironmentInputDTO
from src.domain.entities.environment import Environment
from src.domain.ports.repositories import (
    IEnvironmentRepository,
    IProjectRepository,
    IServerRepository,
)
from src.domain.value_objects.environment_type import EnvironmentType


class LinkEnvironment:
    def __init__(
        self,
        project_repo: IProjectRepository,
        server_repo: IServerRepository,
        environment_repo: IEnvironmentRepository,
    ) -> None:
        self.project_repo = project_repo
        self.server_repo = server_repo
        self.environment_repo = environment_repo

    async def execute(self, dto: LinkEnvironmentInputDTO) -> Environment:
        project = await self.project_repo.get_by_id(dto.project_id)
        if project is None:
            raise NotFoundAppError("Project not found")

        server = await self.server_repo.get_by_id(dto.server_id)
        if server is None:
            raise NotFoundAppError("Server not found")

        env = Environment.create(
            project_id=str(dto.project_id),
            name=dto.name,
            environment_type=EnvironmentType(dto.environment_type),
            server_id=str(dto.server_id),
            working_directory=dto.working_directory,
        )

        return await self.environment_repo.create(env)
