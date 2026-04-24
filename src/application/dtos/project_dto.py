from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True, frozen=True)
class CreateProjectInputDTO:
    name: str
    repo_github: str
    tech_stack: str
    created_by: UUID


@dataclass(slots=True, frozen=True)
class ProjectOutputDTO:
    id: UUID
    name: str
    repo_github: str
    tech_stack: str
    created_by: UUID


@dataclass(slots=True, frozen=True)
class LinkEnvironmentInputDTO:
    project_id: UUID
    name: str
    environment_type: str
    server_id: UUID
    working_directory: str


@dataclass(slots=True, frozen=True)
class UpdateProjectInputDTO:
    name: str
    repo_github: str
    tech_stack: str


@dataclass(slots=True, frozen=True)
class UpdateEnvironmentInputDTO:
    name: str
    environment_type: str
    server_id: UUID
    working_directory: str
    is_active: bool
