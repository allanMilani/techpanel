import pytest
from src.domain.entities.pipeline_step import PipelineStep
from src.domain.errors import ValidationError
from src.domain.value_objects.on_failure_policy import OnFailurePolicy
from src.domain.value_objects.step_type import StepType


def test_should_create_pipeline_step_successfully() -> None:
    step = PipelineStep.create(
        pipeline_id="00000000-0000-0000-0000-000000000001",
        order=1,
        name="Git pull",
        step_type=StepType.SSH_COMMAND,
        command="git pull",
        on_failure=OnFailurePolicy.STOP,
    )
    assert step.order == 1


def test_should_raise_validation_error_if_order_is_less_than_1() -> None:
    with pytest.raises(ValidationError):
        PipelineStep.create(
            pipeline_id="00000000-0000-0000-0000-000000000001",
            order=0,
            name="Invalid",
            step_type=StepType.SSH_COMMAND,
            command="x",
            on_failure=OnFailurePolicy.STOP,
        )