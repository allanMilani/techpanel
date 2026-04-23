from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import Pipeline, PipelineStep
from src.domain.ports.repositories import IPipelineRepository
from src.infrastructure.persistence.mappers import (
    pipeline_model_to_entity,
    pipeline_step_entity_fields_for_insert,
    pipeline_step_model_to_entity,
)
from src.infrastructure.persistence.models import PipelineModel, PipelineStepModel
from src.infrastructure.persistence.models.environment_model import EnvironmentModel
from src.infrastructure.persistence.models.project_model import ProjectModel


class PgPipelineRepository(IPipelineRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, pipeline: Pipeline) -> Pipeline:
        creator_result = await self._session.execute(
            select(ProjectModel.created_by)
            .join(EnvironmentModel, EnvironmentModel.project_id == ProjectModel.id)
            .where(EnvironmentModel.id == pipeline.environment_id)
        )
        created_by = creator_result.scalar_one_or_none()
        if created_by is None:
            raise ValueError(
                f"Could not resolve pipeline creator from environment {pipeline.environment_id}"
            )

        row = PipelineModel(
            id=pipeline.id,
            environment_id=pipeline.environment_id,
            name=pipeline.name,
            description=pipeline.description,
            created_by=created_by,
        )
        self._session.add(row)
        await self._session.flush()
        return pipeline_model_to_entity(row, [])

    async def update(self, pipeline: Pipeline) -> Pipeline:
        result = await self._session.execute(
            select(PipelineModel).where(PipelineModel.id == pipeline.id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise ValueError(f"Pipeline with id {pipeline.id} not found")

        row.environment_id = pipeline.environment_id
        row.name = pipeline.name
        row.description = pipeline.description
        await self._session.flush()

        steps = await self.list_steps(pipeline.id)
        return Pipeline(
            id=row.id,
            environment_id=row.environment_id,
            name=row.name,
            description=row.description,
            steps=tuple(steps),
        )

    async def get_by_id(self, pipeline_id: UUID) -> Pipeline | None:
        result = await self._session.execute(
            select(PipelineModel).where(PipelineModel.id == pipeline_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        step_rows = await self._session.execute(
            select(PipelineStepModel).where(
                PipelineStepModel.pipeline_id == pipeline_id
            )
        )
        return pipeline_model_to_entity(row, list(step_rows.scalars().all()))

    async def list_by_environment(self, environment_id: UUID) -> list[Pipeline]:
        result = await self._session.execute(
            select(PipelineModel).where(PipelineModel.environment_id == environment_id)
        )
        rows = result.scalars().all()
        pipelines: list[Pipeline] = []
        for row in rows:
            step_rows = await self._session.execute(
                select(PipelineStepModel).where(PipelineStepModel.pipeline_id == row.id)
            )
            pipelines.append(
                pipeline_model_to_entity(row, list(step_rows.scalars().all()))
            )
        return pipelines

    async def delete(self, pipeline_id: UUID) -> None:
        result = await self._session.execute(
            select(PipelineModel).where(PipelineModel.id == pipeline_id)
        )
        row = result.scalar_one_or_none()
        if row is not None:
            await self._session.delete(row)

    async def add_step(self, step: PipelineStep) -> PipelineStep:
        row = PipelineStepModel(**pipeline_step_entity_fields_for_insert(step))
        self._session.add(row)
        await self._session.flush()
        return pipeline_step_model_to_entity(row)

    async def update_step(self, step: PipelineStep) -> PipelineStep:
        result = await self._session.execute(
            select(PipelineStepModel).where(PipelineStepModel.id == step.id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise ValueError(f"Pipeline step with id {step.id} not found")

        row.pipeline_id = step.pipeline_id
        row.order = step.order
        row.name = step.name
        row.type = step.step_type.value
        row.command = step.command
        row.on_failure = step.on_failure.value
        row.timeout_seconds = step.timeout_seconds
        row.working_directory = step.working_directory
        row.is_active = step.is_active
        await self._session.flush()
        return pipeline_step_model_to_entity(row)

    async def remove_step(self, step_id: UUID) -> None:
        result = await self._session.execute(
            select(PipelineStepModel).where(PipelineStepModel.id == step_id)
        )
        row = result.scalar_one_or_none()
        if row is not None:
            await self._session.delete(row)

    async def list_steps(self, pipeline_id: UUID) -> list[PipelineStep]:
        result = await self._session.execute(
            select(PipelineStepModel)
            .where(PipelineStepModel.pipeline_id == pipeline_id)
            .order_by(PipelineStepModel.order.asc())
        )
        return [pipeline_step_model_to_entity(r) for r in result.scalars().all()]

    async def get_next_step(
        self, pipeline_id: UUID, after_order: int
    ) -> PipelineStep | None:
        result = await self._session.execute(
            select(PipelineStepModel)
            .where(PipelineStepModel.pipeline_id == pipeline_id)
            .where(PipelineStepModel.order > after_order)
            .where(PipelineStepModel.is_active.is_(True))
            .order_by(PipelineStepModel.order.asc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        return pipeline_step_model_to_entity(row) if row else None
