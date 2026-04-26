import pytest

from src.application import ValidationAppError
from src.domain.value_objects.step_type import StepType
from src.infrastructure.runners.runner_registry import RunnerRegistry
from tests.unit.application.fakes import FakeRunner


def test_runner_registry_returns_runner_by_type() -> None:
    registry = RunnerRegistry(
        runners={
            StepType.SSH_COMMAND: FakeRunner(),
            StepType.HTTP_HEALTHCHECK: FakeRunner(),
            StepType.NOTIFY_WEBHOOK: FakeRunner(),
        }
    )
    runner = registry.get(StepType.SSH_COMMAND)
    assert runner is not None


def test_runner_registry_raises_for_missing_type() -> None:
    registry = RunnerRegistry(runners={})
    with pytest.raises(ValidationAppError):
        registry.get(StepType.SSH_COMMAND)
