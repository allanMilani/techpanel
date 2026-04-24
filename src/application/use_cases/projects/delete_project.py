from uuid import UUID

from src.application import NotFoundAppError
from src.domain.ports.repositories import IProjectRepository


class DeleteProject:
    def __init__(self, project_repo: IProjectRepository) -> None:
        self.project_repo = project_repo

    async def execute(self, project_id: UUID) -> None:
        existing = await self.project_repo.get_by_id(project_id)
        if existing is None:
            raise NotFoundAppError("Project not found")

        await self.project_repo.delete(project_id)
