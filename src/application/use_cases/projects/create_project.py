from src.application.dtos import CreateProjectInputDTO, ProjectOutputDTO
from src.domain.entities.project import Project
from src.domain.ports.repositories import IProjectRepository


class CreateProject:
    def __init__(self, project_repo: IProjectRepository) -> None:
        self.project_repo = project_repo

    async def execute(self, dto: CreateProjectInputDTO) -> ProjectOutputDTO:
        project = Project.create(
            name=dto.name,
            repo_github=dto.repo_github,
            tech_stack=dto.tech_stack,
            created_by=str(dto.created_by),
        )
        created = await self.project_repo.create(project)
        return ProjectOutputDTO(
            id=created.id,
            name=created.name,
            repo_github=created.repo_github,
            tech_stack=created.tech_stack,
            created_by=created.created_by,
        )
