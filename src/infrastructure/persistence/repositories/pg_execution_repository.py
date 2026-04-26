from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import Execution
from src.domain.ports.repositories import IExecutionRepository
from src.infrastructure.persistence.mappers import execution_model_to_entity
from src.infrastructure.persistence.models import ExecutionModel, PipelineModel, EnvironmentModel
from src.infrastructure.persistence.models.enums import (
    ExecutionStatus as ExecutionStatusModel,
)


ACTIVE_EXECUTION_STATUSES = (
    ExecutionStatusModel.PENDING,
    ExecutionStatusModel.RUNNING,
    ExecutionStatusModel.BLOCKED,
)


class PgExecutionRepository(IExecutionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, execution: Execution) -> Execution:
        row = ExecutionModel(
            id=execution.id,
            pipeline_id=execution.pipeline_id,
            triggered_by=execution.triggered_by,
            branch_or_tag=execution.branch_or_tag,
            status=execution.status.value,
        )
        self._session.add(row)
        await self._session.flush()
        return execution_model_to_entity(row)

    async def update(self, execution: Execution) -> Execution:
        result = await self._session.execute(
            select(ExecutionModel).where(ExecutionModel.id == execution.id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise ValueError(f"Execution with id {execution.id} not found")

        row.pipeline_id = execution.pipeline_id
        row.triggered_by = execution.triggered_by
        row.branch_or_tag = execution.branch_or_tag
        row.status = execution.status.value
        await self._session.flush()
        return execution_model_to_entity(row)

    async def get_by_id(self, execution_id: UUID) -> Execution | None:
        result = await self._session.execute(
            select(ExecutionModel).where(ExecutionModel.id == execution_id)
        )
        row = result.scalar_one_or_none()
        return execution_model_to_entity(row) if row else None

    async def list_by_pipeline(self, pipeline_id: UUID) -> list[Execution]:
        result = await self._session.execute(
            select(ExecutionModel).where(ExecutionModel.pipeline_id == pipeline_id)
        )
        return [execution_model_to_entity(row) for row in result.scalars().all()]

    async def get_active_execution_for_environment(
        self, environment_id: UUID
    ) -> Execution | None:
        result = await self._session.execute(
            select(ExecutionModel)
            .join(PipelineModel, PipelineModel.id == ExecutionModel.pipeline_id)
            .where(PipelineModel.environment_id == environment_id)
            .where(ExecutionModel.status.in_(ACTIVE_EXECUTION_STATUSES))
            .order_by(ExecutionModel.id.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        return execution_model_to_entity(row) if row else None

    async def get_active_execution_for_project(
        self, project_id: UUID
    ) -> Execution | None:
        result = await self._session.execute(
            select(ExecutionModel)
            .join(PipelineModel, PipelineModel.id == ExecutionModel.pipeline_id)
            .join(EnvironmentModel, EnvironmentModel.id == PipelineModel.environment_id)
            .where(EnvironmentModel.project_id == project_id)
            .where(ExecutionModel.status.in_(ACTIVE_EXECUTION_STATUSES))
            .order_by(ExecutionModel.id.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        return execution_model_to_entity(row) if row else None