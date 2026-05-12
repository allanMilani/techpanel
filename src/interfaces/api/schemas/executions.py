from datetime import datetime

from pydantic import BaseModel


class StartExecutionRequest(BaseModel):
    pipeline_id: str
    branch_or_tag: str


class ExecutionResponse(BaseModel):
    id: str
    pipeline_id: str
    branch_or_tag: str
    status: str
    created_at: datetime


class StepExecutionResponse(BaseModel):
    id: str
    execution_id: str
    pipeline_step_id: str | None = None
    order: int
    status: str
    log_output: str | None
    exit_code: int | None
    command: str | None = None


class ExecutionPanelResponse(BaseModel):
    error: str | None = None
    execution: ExecutionResponse | None = None
    step_logs: list[StepExecutionResponse]
    step_labels: dict[str, str]
    terminal: bool
    workspace_prepare_log: str | None = None
    workspace_prepare_exit_code: int | None = None
    workspace_prepare_skipped: bool = False
