from __future__ import annotations

from src.domain.entities.pipeline import Pipeline
from src.infrastructure.persistence.models.pipeline_model import PipelineModel
from src.infrastructure.persistence.mappers.pipeline_step_mapper import (
    pipeline_step_model_to_entity,
)


def pipeline_model_to_entity(row: PipelineModel, steps: list) -> Pipeline:
    step_entities = tuple(
        pipeline_step_model_to_entity(s) for s in sorted(steps, key=lambda x: x.order)
    )
    return Pipeline(
        id=row.id,
        environment_id=row.environment_id,
        name=row.name,
        description=row.description,
        steps=step_entities,
    )
