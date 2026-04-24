from typing import Annotated

from fastapi import Depends

from src.application.use_cases.projects.create_project import CreateProject
from src.application.use_cases.projects.delete_project import DeleteProject
from src.application.use_cases.projects.get_project import GetProject
from src.application.use_cases.projects.link_environment import LinkEnvironment
from src.application.use_cases.projects.list_project_environments import (
    ListProjectEnvironments,
)
from src.application.use_cases.projects.list_projects import ListProjects
from src.application.use_cases.projects.update_environment import UpdateEnvironment
from src.application.use_cases.projects.update_project import UpdateProject
from src.domain.ports.repositories import (
    IEnvironmentRepository,
    IProjectRepository,
    IServerRepository,
)
from src.interfaces.api.dependencies.core import (
    get_environment_repository,
    get_project_repository,
    get_server_repository,
)


def get_create_project(
    project_repo: Annotated[IProjectRepository, Depends(get_project_repository)],
) -> CreateProject:
    return CreateProject(project_repo=project_repo)


def get_list_projects(
    project_repo: Annotated[IProjectRepository, Depends(get_project_repository)],
) -> ListProjects:
    return ListProjects(project_repo=project_repo)


def get_get_project(
    project_repo: Annotated[IProjectRepository, Depends(get_project_repository)],
) -> GetProject:
    return GetProject(project_repo=project_repo)


def get_update_project(
    project_repo: Annotated[IProjectRepository, Depends(get_project_repository)],
) -> UpdateProject:
    return UpdateProject(project_repo=project_repo)


def get_delete_project(
    project_repo: Annotated[IProjectRepository, Depends(get_project_repository)],
) -> DeleteProject:
    return DeleteProject(project_repo=project_repo)


def get_link_environment(
    project_repo: Annotated[IProjectRepository, Depends(get_project_repository)],
    server_repo: Annotated[IServerRepository, Depends(get_server_repository)],
    environment_repo: Annotated[
        IEnvironmentRepository, Depends(get_environment_repository)
    ],
) -> LinkEnvironment:
    return LinkEnvironment(
        project_repo=project_repo,
        server_repo=server_repo,
        environment_repo=environment_repo,
    )


def get_list_project_environments(
    project_repo: Annotated[IProjectRepository, Depends(get_project_repository)],
    environment_repo: Annotated[
        IEnvironmentRepository, Depends(get_environment_repository)
    ],
) -> ListProjectEnvironments:
    return ListProjectEnvironments(
        project_repo=project_repo,
        environment_repo=environment_repo,
    )


def get_update_environment(
    project_repo: Annotated[IProjectRepository, Depends(get_project_repository)],
    server_repo: Annotated[IServerRepository, Depends(get_server_repository)],
    environment_repo: Annotated[
        IEnvironmentRepository, Depends(get_environment_repository)
    ],
) -> UpdateEnvironment:
    return UpdateEnvironment(
        project_repo=project_repo,
        server_repo=server_repo,
        environment_repo=environment_repo,
    )
