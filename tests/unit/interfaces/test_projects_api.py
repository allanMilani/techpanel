from dataclasses import replace
from uuid import uuid4

from fastapi.testclient import TestClient

from main import app
from src.application.dtos import ProjectOutputDTO
from src.application.dtos.pagination_dto import PaginatedResult
from src.domain.entities.environment import Environment
from src.domain.value_objects.environment_type import EnvironmentType
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
)


def test_projects_crud_routes() -> None:
    project_id = uuid4()
    created_by = uuid4()
    current_project = ProjectOutputDTO(
        id=project_id,
        name="platform",
        repo_github="https://github.com/org/platform",
        tech_stack="python",
        created_by=created_by,
    )

    class ListProjectsStub:
        async def execute(self, page: int, per_page: int) -> PaginatedResult[ProjectOutputDTO]:
            return PaginatedResult(
                items=[current_project],
                total=1,
                page=page,
                per_page=per_page,
            )

    class CreateProjectStub:
        async def execute(self, _dto) -> ProjectOutputDTO:
            return current_project

    class GetProjectStub:
        async def execute(self, _project_id) -> ProjectOutputDTO:
            return current_project

    class UpdateProjectStub:
        async def execute(self, _project_id, _dto) -> ProjectOutputDTO:
            return replace(current_project, name="platform-v2")

    class DeleteProjectStub:
        async def execute(self, _project_id) -> None:
            return None

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        sub=str(created_by), role="admin"
    )
    app.dependency_overrides[get_list_projects] = lambda: ListProjectsStub()
    app.dependency_overrides[get_create_project] = lambda: CreateProjectStub()
    app.dependency_overrides[get_get_project] = lambda: GetProjectStub()
    app.dependency_overrides[get_update_project] = lambda: UpdateProjectStub()
    app.dependency_overrides[get_delete_project] = lambda: DeleteProjectStub()

    with TestClient(app) as client:
        list_response = client.get(
            "/api/projects/",
            headers={"Authorization": "Bearer test"},
        )
        assert list_response.status_code == 200
        assert list_response.json()["items"][0]["id"] == str(project_id)

        create_response = client.post(
            "/api/projects/",
            headers={"Authorization": "Bearer test"},
            json={
                "name": "platform",
                "repo_github": "https://github.com/org/platform",
                "tech_stack": "python",
            },
        )
        assert create_response.status_code == 201
        assert create_response.json()["name"] == "platform"

        get_response = client.get(
            f"/api/projects/{project_id}",
            headers={"Authorization": "Bearer test"},
        )
        assert get_response.status_code == 200
        assert get_response.json()["repo_github"] == "https://github.com/org/platform"

        update_response = client.put(
            f"/api/projects/{project_id}",
            headers={"Authorization": "Bearer test"},
            json={
                "name": "platform-v2",
                "repo_github": "https://github.com/org/platform",
                "tech_stack": "python",
            },
        )
        assert update_response.status_code == 200
        assert update_response.json()["name"] == "platform-v2"

        delete_response = client.delete(
            f"/api/projects/{project_id}",
            headers={"Authorization": "Bearer test"},
        )
        assert delete_response.status_code == 204

    app.dependency_overrides.clear()


def test_project_with_staging_and_production_is_listed_via_api() -> None:
    project_id = uuid4()
    server_id = uuid4()
    env_staging = Environment.create(
        project_id=str(project_id),
        name="staging",
        environment_type=EnvironmentType.STAGING,
        server_id=str(server_id),
        working_directory="/var/www/app-stg",
    )
    env_production = Environment.create(
        project_id=str(project_id),
        name="production",
        environment_type=EnvironmentType.PRODUCTION,
        server_id=str(server_id),
        working_directory="/var/www/app-prd",
    )
    created_envs: list[Environment] = []

    class LinkEnvironmentStub:
        async def execute(self, dto) -> Environment:
            if dto.environment_type == EnvironmentType.STAGING.value:
                created_envs.append(env_staging)
                return env_staging
            created_envs.append(env_production)
            return env_production

    class ListProjectEnvironmentsStub:
        async def execute(self, _project_id, page: int, per_page: int):
            return PaginatedResult(
                items=created_envs,
                total=len(created_envs),
                page=page,
                per_page=per_page,
            )

    class UpdateEnvironmentStub:
        async def execute(self, _project_id, _environment_id, _dto):
            return env_staging

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        sub=str(uuid4()), role="admin"
    )
    app.dependency_overrides[get_link_environment] = lambda: LinkEnvironmentStub()
    app.dependency_overrides[get_list_project_environments] = lambda: (
        ListProjectEnvironmentsStub()
    )
    app.dependency_overrides[get_update_environment] = lambda: UpdateEnvironmentStub()

    with TestClient(app) as client:
        create_staging = client.post(
            f"/api/projects/{project_id}/environments",
            headers={"Authorization": "Bearer test"},
            json={
                "name": "staging",
                "environment_type": "staging",
                "server_id": str(server_id),
                "working_directory": "/var/www/app-stg",
            },
        )
        assert create_staging.status_code == 201

        create_production = client.post(
            f"/api/projects/{project_id}/environments",
            headers={"Authorization": "Bearer test"},
            json={
                "name": "production",
                "environment_type": "production",
                "server_id": str(server_id),
                "working_directory": "/var/www/app-prd",
            },
        )
        assert create_production.status_code == 201

        list_response = client.get(
            f"/api/projects/{project_id}/environments",
            headers={"Authorization": "Bearer test"},
        )
        assert list_response.status_code == 200
        body = list_response.json()
        assert len(body["items"]) == 2
        listed_types = {env["environment_type"] for env in body["items"]}
        assert listed_types == {"staging", "production"}

    app.dependency_overrides.clear()
