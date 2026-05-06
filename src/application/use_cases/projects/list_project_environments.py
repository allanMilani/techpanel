from uuid import UUID

from src.application import NotFoundAppError
from src.application.dtos.pagination_dto import PaginatedResult, offset_for_page
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

    async def execute(
        self, project_id: UUID, page: int, per_page: int
    ) -> PaginatedResult[Environment]:
        project = await self.project_repo.get_by_id(project_id)
        if project is None:
            raise NotFoundAppError("Project not found")

        offset = offset_for_page(page, per_page)
        items, total = await self.environment_repo.list_by_project_page(
            project_id, per_page, offset
        )
        return PaginatedResult(
            items=items, total=total, page=page, per_page=per_page
        )
