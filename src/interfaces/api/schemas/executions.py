from pydantic import BaseModel


class StartExecutionRequest(BaseModel):
    pipeline_id: str
    branch_or_tag: str


class ExecutionResponse(BaseModel):
    id: str
    pipeline_id: str
    branch_or_tag: str
    status: str
