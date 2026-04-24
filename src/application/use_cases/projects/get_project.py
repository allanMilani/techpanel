from uuid import UUID

from src.application import NotFoundAppError
from src.application.dtos import ProjectOutputDTO
from src.domain.ports.repositories import IProjectRepository


class GetProject:
    def __init__(self, project_repo: IProjectRepository) -> None:
        self.project_repo = project_repo

    async def execute(self, project_id: UUID) -> ProjectOutputDTO:
        project = await self.project_repo.get_by_id(project_id)

        if project is None:
            raise NotFoundAppError("Project not found")

        return ProjectOutputDTO(
            id=project.id,
            name=project.name,
            repo_github=project.repo_github,
            tech_stack=project.tech_stack,
            created_by=project.created_by,
        )
