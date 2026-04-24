from uuid import UUID

from src.application import NotFoundAppError
from src.application.dtos import ProjectOutputDTO, UpdateProjectInputDTO
from src.domain.entities.project import Project
from src.domain.ports.repositories import IProjectRepository


class UpdateProject:
    def __init__(self, project_repo: IProjectRepository) -> None:
        self.project_repo = project_repo

    async def execute(
        self, project_id: UUID, dto: UpdateProjectInputDTO
    ) -> ProjectOutputDTO:
        project = await self.project_repo.get_by_id(project_id)
        if project is None:
            raise NotFoundAppError("Project not found")

        updated = Project(
            id=project.id,
            name=dto.name.strip().lower(),
            repo_github=dto.repo_github.strip(),
            tech_stack=dto.tech_stack.strip(),
            created_by=project.created_by,
        )

        persisted = await self.project_repo.update(updated)
        return ProjectOutputDTO(
            id=persisted.id,
            name=persisted.name,
            repo_github=persisted.repo_github,
            tech_stack=persisted.tech_stack,
            created_by=persisted.created_by,
        )
