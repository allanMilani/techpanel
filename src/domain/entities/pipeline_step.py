from dataclasses import dataclass
from uuid import UUID, uuid4

from src.domain.errors import ValidationError
from src.domain.value_objects.step_type import StepType
from src.domain.value_objects.on_failure_policy import OnFailurePolicy


@dataclass(slots=True, frozen=True)
class PipelineStep:
    id: UUID
    pipeline_id: UUID
    order: int
    name: str
    step_type: StepType
    command: str
    on_failure: OnFailurePolicy
    timeout_seconds: int = 300
    working_directory: str | None = None
    is_active: bool = True

    @staticmethod
    def create(
        pipeline_id: str,
        order: int,
        name: str,
        step_type: StepType,
        command: str,
        on_failure: OnFailurePolicy,
        timeout_seconds: int = 300,
        working_directory: str | None = None,
        is_active: bool = True,
    ) -> "PipelineStep":

        if not pipeline_id:
            raise ValidationError("Pipeline ID is required")

        if not order:
            raise ValidationError("Order is required")

        if not name.strip():
            raise ValidationError("Name is required")

        if not step_type:
            raise ValidationError("Step type is required")

        if not command.strip():
            raise ValidationError("Command is required")

        if not on_failure:
            raise ValidationError("On failure policy is required")

        if order < 1:
            raise ValidationError("Order must be greater than or equal to 1")

        if timeout_seconds < 1:
            raise ValidationError("Timeout must be greater than or equal to 1")

        if (
            working_directory is not None
            and working_directory.strip()
            and not working_directory.startswith("/")
        ):
            raise ValidationError("Working directory must start with a slash")

        return PipelineStep(
            id=uuid4(),
            pipeline_id=UUID(pipeline_id),
            order=order,
            name=name.strip(),
            step_type=step_type,
            command=command.strip(),
            on_failure=on_failure,
            timeout_seconds=timeout_seconds,
            working_directory=working_directory.strip() if working_directory else None,
            is_active=is_active,
        )
