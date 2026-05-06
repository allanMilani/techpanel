from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from src.application.dtos import (
    CreateProjectInputDTO,
    LinkEnvironmentInputDTO,
    ProjectOutputDTO,
    UpdateEnvironmentInputDTO,
    UpdateProjectInputDTO,
)
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
from src.interfaces.api.dependencies import (
    CurrentUser,
    get_create_project,
    get_current_user,
    get_delete_project,
    get_get_project,
    get_link_environment,
    get_list_project_environments,
    get_list_projects,
    get_update_environment,
    get_update_project,
    require_admin,
)
from src.interfaces.api.dependencies.pagination import Pagination, get_pagination
from src.interfaces.api.schemas.paged_lists import (
    EnvironmentsListPageResponse,
    ProjectsListPageResponse,
)
from src.interfaces.api.schemas.environment_schemas import (
    EnvironmentCreateBody,
    EnvironmentResponse,
    EnvironmentUpdateBody,
)
from src.interfaces.api.schemas.project_schemas import (
    ProjectCreateBody,
    ProjectResponse,
    ProjectUpdateBody,
)

router = APIRouter(prefix="/projects", tags=["projects"])


def _project_to_response(dto: ProjectOutputDTO) -> ProjectResponse:
    return ProjectResponse(
        id=dto.id,
        name=dto.name,
        repo_github=dto.repo_github,
        tech_stack=dto.tech_stack,
        created_by=dto.created_by,
    )


def _env_to_response(env) -> EnvironmentResponse:
    return EnvironmentResponse(
        id=env.id,
        project_id=env.project_id,
        name=env.name,
        environment_type=env.environment_type.value,
        server_id=env.server_id,
        working_directory=env.working_directory,
        is_active=env.is_active,
    )


@router.get("/", response_model=ProjectsListPageResponse)
async def list_projects(
    _: Annotated[CurrentUser, Depends(get_current_user)],
    pagination: Annotated[Pagination, Depends(get_pagination)],
    use_case: Annotated[ListProjects, Depends(get_list_projects)],
) -> ProjectsListPageResponse:
    out = await use_case.execute(pagination.page, pagination.per_page)
    return ProjectsListPageResponse(
        items=[_project_to_response(p) for p in out.items],
        total=out.total,
        page=out.page,
        per_page=out.per_page,
        total_pages=out.total_pages,
    )


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreateBody,
    current_user: Annotated[CurrentUser, Depends(require_admin)],
    use_case: Annotated[CreateProject, Depends(get_create_project)],
) -> ProjectResponse:
    dto = CreateProjectInputDTO(
        name=payload.name,
        repo_github=payload.repo_github,
        tech_stack=payload.tech_stack,
        created_by=UUID(current_user.sub),
    )

    out = await use_case.execute(dto)
    return _project_to_response(out)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    _: Annotated[CurrentUser, Depends(get_current_user)],
    use_case: Annotated[GetProject, Depends(get_get_project)],
) -> ProjectResponse:
    out = await use_case.execute(project_id)
    return _project_to_response(out)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    payload: ProjectUpdateBody,
    _: Annotated[CurrentUser, Depends(require_admin)],
    use_case: Annotated[UpdateProject, Depends(get_update_project)],
) -> ProjectResponse:
    dto = UpdateProjectInputDTO(
        name=payload.name,
        repo_github=payload.repo_github,
        tech_stack=payload.tech_stack,
    )

    out = await use_case.execute(project_id, dto)
    return _project_to_response(out)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    _: Annotated[CurrentUser, Depends(require_admin)],
    use_case: Annotated[DeleteProject, Depends(get_delete_project)],
) -> None:
    await use_case.execute(project_id)


@router.get("/{project_id}/environments", response_model=EnvironmentsListPageResponse)
async def list_project_environments(
    project_id: UUID,
    _: Annotated[CurrentUser, Depends(get_current_user)],
    pagination: Annotated[Pagination, Depends(get_pagination)],
    use_case: Annotated[
        ListProjectEnvironments, Depends(get_list_project_environments)
    ],
) -> EnvironmentsListPageResponse:
    out = await use_case.execute(project_id, pagination.page, pagination.per_page)
    return EnvironmentsListPageResponse(
        items=[_env_to_response(env) for env in out.items],
        total=out.total,
        page=out.page,
        per_page=out.per_page,
        total_pages=out.total_pages,
    )


@router.post(
    "/{project_id}/environments",
    response_model=EnvironmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_environment(
    project_id: UUID,
    payload: EnvironmentCreateBody,
    _: Annotated[CurrentUser, Depends(require_admin)],
    use_case: Annotated[LinkEnvironment, Depends(get_link_environment)],
) -> EnvironmentResponse:
    dto = LinkEnvironmentInputDTO(
        project_id=project_id,
        name=payload.name,
        environment_type=payload.environment_type,
        server_id=payload.server_id,
        working_directory=payload.working_directory,
    )

    out = await use_case.execute(dto)
    return _env_to_response(out)


@router.put(
    "/{project_id}/environments/{environment_id}", response_model=EnvironmentResponse
)
async def update_environment(
    project_id: UUID,
    environment_id: UUID,
    payload: EnvironmentUpdateBody,
    _: Annotated[CurrentUser, Depends(require_admin)],
    use_case: Annotated[UpdateEnvironment, Depends(get_update_environment)],
) -> EnvironmentResponse:
    dto = UpdateEnvironmentInputDTO(
        name=payload.name,
        environment_type=payload.environment_type,
        server_id=payload.server_id,
        working_directory=payload.working_directory,
        is_active=payload.is_active,
    )

    env = await use_case.execute(project_id, environment_id, dto)
    return _env_to_response(env)
