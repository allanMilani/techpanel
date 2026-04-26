from src.application import ValidationAppError
from src.domain.ports.services.i_runner_registry import IRunnerRegistry
from src.domain.ports.services import IStepRunner
from src.domain.value_objects.step_type import StepType


class RunnerRegistry(IRunnerRegistry):
    def __init__(self, runners: dict[StepType, IStepRunner]) -> None:
        self.runners = runners

    def get(self, step_type: StepType) -> IStepRunner:
        runner = self.runners.get(step_type)
        if runner is None:
            raise ValidationAppError(
                f"No runner registered for step type: {step_type.value}"
            )
        return runner
