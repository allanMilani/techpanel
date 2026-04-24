from uuid import UUID

from pydantic import BaseModel


class ProjectCreateBody(BaseModel):
    name: str
    repo_github: str
    tech_stack: str


class ProjectUpdateBody(BaseModel):
    name: str
    repo_github: str
    tech_stack: str


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    repo_github: str
    tech_stack: str
    created_by: UUID

    model_config = {"from_attributes": True}
