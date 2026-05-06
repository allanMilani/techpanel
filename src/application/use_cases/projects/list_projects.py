from src.application.dtos import ProjectOutputDTO
from src.application.dtos.pagination_dto import PaginatedResult, offset_for_page
from src.domain.ports.repositories import IProjectRepository


class ListProjects:
    def __init__(self, project_repo: IProjectRepository) -> None:
        self.project_repo = project_repo

    async def execute(self, page: int, per_page: int) -> PaginatedResult[ProjectOutputDTO]:
        offset = offset_for_page(page, per_page)
        projects, total = await self.project_repo.list_all_page(per_page, offset)
        items = [
            ProjectOutputDTO(
                id=project.id,
                name=project.name,
                repo_github=project.repo_github,
                tech_stack=project.tech_stack,
                created_by=project.created_by,
            )
            for project in projects
        ]
        return PaginatedResult(
            items=items, total=total, page=page, per_page=per_page
        )
