from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import StepExecution
from src.domain.ports.repositories import IStepExecutionRepository
from src.domain.value_objects.step_execution_status import StepExecutionStatus
from src.infrastructure.persistence.mappers import step_execution_model_to_entity
from src.infrastructure.persistence.models import StepExecutionModel


class PgStepExecutionRepository(IStepExecutionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_many(self, steps: list[StepExecution]) -> list[StepExecution]:
        rows = [
            StepExecutionModel(
                id=step.id,
                execution_id=step.execution_id,
                pipeline_step_id=step.pipeline_step_id,
                order=step.order,
                status=step.status.value,
                log_output=step.log_output,
                exit_code=step.exit_code,
                started_at=step.started_at,
                finished_at=step.finished_at,
            )
            for step in steps
        ]
        self._session.add_all(rows)
        await self._session.flush()
        return [step_execution_model_to_entity(row) for row in rows]

    async def update(self, step_execution: StepExecution) -> StepExecution:
        result = await self._session.execute(
            select(StepExecutionModel).where(StepExecutionModel.id == step_execution.id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise ValueError(f"Step execution with id {step_execution.id} not found")

        row.status = step_execution.status.value
        row.log_output = step_execution.log_output
        row.exit_code = step_execution.exit_code
        row.started_at = step_execution.started_at
        row.finished_at = step_execution.finished_at
        await self._session.flush()
        return step_execution_model_to_entity(row)

    async def get_by_id(self, step_execution_id: UUID) -> StepExecution | None:
        result = await self._session.execute(
            select(StepExecutionModel).where(StepExecutionModel.id == step_execution_id)
        )
        row = result.scalar_one_or_none()
        return step_execution_model_to_entity(row) if row else None

    async def get_last_by_execution(self, execution_id: UUID) -> StepExecution | None:
        result = await self._session.execute(
            select(StepExecutionModel)
            .where(StepExecutionModel.execution_id == execution_id)
            .order_by(StepExecutionModel.order.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        return step_execution_model_to_entity(row) if row else None

    async def list_by_execution(self, execution_id: UUID) -> list[StepExecution]:
        result = await self._session.execute(
            select(StepExecutionModel)
            .where(StepExecutionModel.execution_id == execution_id)
            .order_by(StepExecutionModel.order.asc())
        )
        return [step_execution_model_to_entity(row) for row in result.scalars().all()]

    async def skip_remaining(self, execution_id: UUID, after_order: int) -> None:
        await self._session.execute(
            update(StepExecutionModel)
            .where(StepExecutionModel.execution_id == execution_id)
            .where(StepExecutionModel.order > after_order)
            .where(StepExecutionModel.status == StepExecutionStatus.PENDING.value)
            .values(
                status=StepExecutionStatus.SKIPPED.value,
                log_output="skipped",
            )
        )
        await self._session.flush()
