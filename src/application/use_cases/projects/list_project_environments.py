from uuid import UUID

from src.application import NotFoundAppError
from src.domain.entities.environment import Environment
from src.domain.ports.repositories import IEnvironmentRepository, IProjectRepository


class ListProjectEnvironments:
    def __init__(
        self,
        project_repo: IProjectRepository,
        environment_repo: IEnvironmentRepository,
    ) -> None:
        self.project_repo = project_repo
        self.environment_repo = environment_repo

    async def execute(self, project_id: UUID) -> list[Environment]:
        project = await self.project_repo.get_by_id(project_id)
        if project is None:
            raise NotFoundAppError("Project not found")

        return await self.environment_repo.list_by_project(project_id)
