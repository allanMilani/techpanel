from uuid import UUID

from pydantic import BaseModel


class EnvironmentCreateBody(BaseModel):
    name: str
    environment_type: str
    server_id: UUID
    working_directory: str


class EnvironmentUpdateBody(BaseModel):
    name: str
    environment_type: str
    server_id: UUID
    working_directory: str
    is_active: bool


class EnvironmentResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    environment_type: str
    server_id: UUID
    working_directory: str
    is_active: bool

    model_config = {"from_attributes": True}
