from __future__ import annotations

from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.ports.repositories import IProjectRepository
from src.domain.entities.project import Project
from src.infrastructure.persistence.models.project_model import ProjectModel
from src.infrastructure.persistence.mappers import project_model_to_entity


class PgProjectRepository(IProjectRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, project: Project) -> Project:
        row = ProjectModel(
            id=project.id,
            name=project.name,
            repo_github=project.repo_github,
            tech_stack=project.tech_stack,
            created_by=project.created_by,
        )

        self._session.add(row)
        await self._session.flush()
        return project_model_to_entity(row)

    async def update(self, project: Project) -> Project:
        result = await self._session.execute(
            select(ProjectModel).where(ProjectModel.id == project.id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise ValueError(f"Project with id {project.id} not found")

        row.name = project.name
        row.repo_github = project.repo_github
        row.tech_stack = project.tech_stack
        row.created_by = project.created_by

        await self._session.flush()
        return project_model_to_entity(row)

    async def get_by_id(self, project_id: UUID) -> Project | None:
        result = await self._session.execute(
            select(ProjectModel).where(ProjectModel.id == project_id)
        )
        row = result.scalar_one_or_none()
        return project_model_to_entity(row) if row else None

    async def list_all(self) -> list[Project]:
        result = await self._session.execute(select(ProjectModel))
        return [project_model_to_entity(row) for row in result.scalars().all()]

    async def delete(self, project_id: UUID) -> None:
        result = await self._session.execute(
            select(ProjectModel).where(ProjectModel.id == project_id)
        )
        row = result.scalar_one_or_none()
        if row:
            await self._session.delete(row)
