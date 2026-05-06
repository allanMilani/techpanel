from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import Execution
from src.domain.ports.repositories import IExecutionRepository
from src.infrastructure.persistence.mappers import execution_model_to_entity
from src.infrastructure.persistence.models import (
    ExecutionModel,
    PipelineModel,
    EnvironmentModel,
)
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
            created_at=execution.created_at,
            triggered_by_ip=execution.triggered_by_ip,
            started_at=execution.started_at,
            finished_at=execution.finished_at,
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
        row.triggered_by_ip = execution.triggered_by_ip
        row.started_at = execution.started_at
        row.finished_at = execution.finished_at
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
            select(ExecutionModel)
            .where(ExecutionModel.pipeline_id == pipeline_id)
            .order_by(ExecutionModel.created_at.desc())
        )
        return [execution_model_to_entity(row) for row in result.scalars().all()]

    async def list_by_pipeline_page(
        self, pipeline_id: UUID, limit: int, offset: int
    ) -> tuple[list[Execution], int]:
        total = int(
            await self._session.scalar(
                select(func.count())
                .select_from(ExecutionModel)
                .where(ExecutionModel.pipeline_id == pipeline_id)
            )
            or 0
        )
        result = await self._session.execute(
            select(ExecutionModel)
            .where(ExecutionModel.pipeline_id == pipeline_id)
            .order_by(ExecutionModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return [execution_model_to_entity(row) for row in result.scalars().all()], total

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
