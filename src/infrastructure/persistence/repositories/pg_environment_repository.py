from __future__ import annotations

from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.ports.repositories import IEnvironmentRepository
from src.domain.entities.environment import Environment
from src.infrastructure.persistence.models.pipeline_model import PipelineModel
from src.infrastructure.persistence.models.environment_model import EnvironmentModel
from src.infrastructure.persistence.mappers import environment_model_to_entity


class PgEnvironmentRepository(IEnvironmentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, environment: Environment) -> Environment:
        row = EnvironmentModel(
            id=environment.id,
            project_id=environment.project_id,
            name=environment.name,
            type=environment.environment_type.value,
            server_id=environment.server_id,
            working_directory=environment.working_directory,
            is_active=environment.is_active,
        )
        self._session.add(row)
        await self._session.flush()
        return environment_model_to_entity(row)

    async def update(self, environment: Environment) -> Environment:
        result = await self._session.execute(
            select(EnvironmentModel).where(EnvironmentModel.id == environment.id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise ValueError(f"Environment with id {environment.id} not found")

        row.name = environment.name
        row.type = environment.environment_type.value
        row.server_id = environment.server_id
        row.working_directory = environment.working_directory
        row.is_active = environment.is_active

        await self._session.flush()
        return environment_model_to_entity(row)

    async def get_by_id(self, environment_id: UUID) -> Environment | None:
        result = await self._session.execute(
            select(EnvironmentModel).where(EnvironmentModel.id == environment_id)
        )
        row = result.scalar_one_or_none()
        return environment_model_to_entity(row) if row else None

    async def list_by_project(self, project_id: UUID) -> list[Environment]:
        result = await self._session.execute(
            select(EnvironmentModel)
            .where(EnvironmentModel.project_id == project_id)
            .order_by(EnvironmentModel.name.asc())
        )
        return [environment_model_to_entity(row) for row in result.scalars().all()]

    async def list_by_pipeline(self, pipeline_id: UUID) -> list[Environment]:
        pipeline_project_result = await self._session.execute(
            select(EnvironmentModel.project_id)
            .join(PipelineModel, PipelineModel.environment_id == EnvironmentModel.id)
            .where(PipelineModel.id == pipeline_id)
        )
        project_id = pipeline_project_result.scalar_one_or_none()
        if project_id is None:
            return []

        result = await self._session.execute(
            select(EnvironmentModel).where(EnvironmentModel.project_id == project_id)
        )
        return [environment_model_to_entity(row) for row in result.scalars().all()]

    async def get_active_by_project(self, project_id: UUID) -> Environment | None:
        result = await self._session.execute(
            select(EnvironmentModel)
            .where(EnvironmentModel.project_id == project_id)
            .where(EnvironmentModel.is_active.is_(True))
            .order_by(EnvironmentModel.name.asc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        return environment_model_to_entity(row) if row else None
