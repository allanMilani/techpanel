from uuid import UUID

from pydantic import BaseModel, Field


class PipelineCreateRequest(BaseModel):
    name: str
    description: str | None = None
    run_git_workspace_sync: bool = False


class PipelineUpdateRequest(BaseModel):
    name: str
    description: str | None = None
    run_git_workspace_sync: bool = False


class PipelineResponse(BaseModel):
    id: UUID
    environment_id: UUID
    name: str
    description: str | None = None
    run_git_workspace_sync: bool = False
    project_id: UUID | None = None
    repo_github: str | None = None
    refs_repository_full_name: str | None = None


class StepCreateRequest(BaseModel):
    order: int | None = Field(default=None, ge=1)
    name: str
    step_type: str
    command: str
    on_failure: str
    timeout_seconds: int = Field(default=300, ge=1)
    working_directory: str | None = None


class StepUpdateRequest(BaseModel):
    name: str
    step_type: str
    command: str
    on_failure: str
    timeout_seconds: int = Field(ge=1)
    working_directory: str | None = None
    is_active: bool


class StepResponse(BaseModel):
    id: UUID
    order: int
    name: str
    step_type: str
    command: str
    on_failure: str
    timeout_seconds: int
    working_directory: str | None
    is_active: bool


class ReorderStepsRequest(BaseModel):
    ordered_step_ids: list[UUID]
