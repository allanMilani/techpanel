from pydantic import BaseModel, Field

from src.interfaces.api.schemas.environment_schemas import EnvironmentResponse
from src.interfaces.api.schemas.executions import ExecutionResponse
from src.interfaces.api.schemas.pipelines import PipelineResponse, StepResponse
from src.interfaces.api.schemas.project_schemas import ProjectResponse
from src.interfaces.api.schemas.servers import ServerResponse
from src.interfaces.api.schemas.github import GitHubRepositoryResponse


class ProjectsListPageResponse(BaseModel):
    items: list[ProjectResponse]
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    per_page: int = Field(..., ge=1)
    total_pages: int = Field(..., ge=0)


class ServersListPageResponse(BaseModel):
    items: list[ServerResponse]
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    per_page: int = Field(..., ge=1)
    total_pages: int = Field(..., ge=0)


class EnvironmentsListPageResponse(BaseModel):
    items: list[EnvironmentResponse]
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    per_page: int = Field(..., ge=1)
    total_pages: int = Field(..., ge=0)


class PipelinesListPageResponse(BaseModel):
    items: list[PipelineResponse]
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    per_page: int = Field(..., ge=1)
    total_pages: int = Field(..., ge=0)


class PipelineStepsPageResponse(BaseModel):
    items: list[StepResponse]
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    per_page: int = Field(..., ge=1)
    total_pages: int = Field(..., ge=0)


class ExecutionHistoryPageResponse(BaseModel):
    items: list[ExecutionResponse]
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    per_page: int = Field(..., ge=1)
    total_pages: int = Field(..., ge=0)


class GitHubRepositoriesPageResponse(BaseModel):
    items: list[GitHubRepositoryResponse]
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    per_page: int = Field(..., ge=1)
    total_pages: int = Field(..., ge=0)
