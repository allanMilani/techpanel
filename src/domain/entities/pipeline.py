from dataclasses import dataclass, replace
from uuid import UUID, uuid4

from src.domain.entities.pipeline_step import PipelineStep
from src.domain.errors import ValidationError


@dataclass(slots=True, frozen=True)
class Pipeline:
    id: UUID
    environment_id: UUID
    name: str
    description: str | None = None
    run_git_workspace_sync: bool = False
    steps: tuple[PipelineStep, ...] = ()

    @staticmethod
    def create(
        name: str,
        environment_id: str,
        description: str | None = None,
        *,
        run_git_workspace_sync: bool = False,
    ) -> "Pipeline":
        if not name.strip():
            raise ValidationError("Name is required")

        if not environment_id:
            raise ValidationError("Environment ID is required")

        return Pipeline(
            id=uuid4(),
            environment_id=UUID(environment_id),
            name=name.strip(),
            description=description,
            run_git_workspace_sync=bool(run_git_workspace_sync),
            steps=(),
        )

    def add_step(self, step: PipelineStep) -> "Pipeline":
        if any(existing.order == step.order for existing in self.steps):
            raise ValidationError("Step order must be unique")

        if step.pipeline_id != self.id:
            raise ValidationError("Step pipeline ID must match pipeline ID")

        return replace(
            self, steps=tuple(sorted((*self.steps, step), key=lambda s: s.order))
        )
