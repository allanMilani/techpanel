from src.application.dtos import ProjectOutputDTO
from src.domain.ports.repositories import IProjectRepository


class ListProjects:
    def __init__(self, project_repo: IProjectRepository) -> None:
        self.project_repo = project_repo

    async def execute(self) -> list[ProjectOutputDTO]:
        projects = await self.project_repo.list_all()
        return [
            ProjectOutputDTO(
                id=project.id,
                name=project.name,
                repo_github=project.repo_github,
                tech_stack=project.tech_stack,
                created_by=project.created_by,
            )
            for project in projects
        ]
