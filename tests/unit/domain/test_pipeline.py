import pytest
from src.domain.entities.pipeline import Pipeline
from src.domain.entities.pipeline_step import PipelineStep
from src.domain.errors import ValidationError
from src.domain.value_objects.on_failure_policy import OnFailurePolicy
from src.domain.value_objects.step_type import StepType


def _step(pipeline_id: str, order: int) -> PipelineStep:
    return PipelineStep.create(
        pipeline_id=pipeline_id,
        order=order,
        name=f"Step {order}",
        step_type=StepType.SSH_COMMAND,
        command="echo ok",
        on_failure=OnFailurePolicy.STOP,
    )


def test_should_add_steps_without_duplicate_order() -> None:
    pipeline = Pipeline.create("Deploy", "00000000-0000-0000-0000-000000000001")
    pipeline_id = str(pipeline.id)
    pipeline = pipeline.add_step(_step(pipeline_id, 1))
    pipeline = pipeline.add_step(_step(pipeline_id, 2))
    assert len(pipeline.steps) == 2


def test_should_raise_validation_error_if_order_is_duplicate() -> None:
    pipeline = Pipeline.create("Deploy", "00000000-0000-0000-0000-000000000001")
    pipeline_id = str(pipeline.id)
    pipeline = pipeline.add_step(_step(pipeline_id, 1))
    with pytest.raises(ValidationError):
        pipeline.add_step(_step(pipeline_id, 1))