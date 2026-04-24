from dataclasses import dataclass
from uuid import uuid4

from fastapi.testclient import TestClient

from main import app
from src.application.dtos import PipelineOutputDTO, PipelineSummaryDTO
from src.interfaces.api.dependencies import (
    CurrentUser,
    get_add_step_use_case,
    get_create_pipeline_use_case,
    get_current_user,
    get_delete_pipeline_use_case,
    get_delete_step_use_case,
    get_get_pipeline_use_case,
    get_list_pipelines_use_case,
    get_reorder_steps_use_case,
    get_update_pipeline_use_case,
    get_update_step_use_case,
)


def test_pipeline_routes_happy_path() -> None:
    env_id = uuid4()
    pipeline_id = uuid4()
    step_id = uuid4()

    @dataclass
    class _CreatePipelineStub:
        async def execute(self, _dto) -> PipelineSummaryDTO:
            return PipelineSummaryDTO(
                id=pipeline_id,
                environment_id=env_id,
                name="deploy",
                description="desc",
            )

    @dataclass
    class _ListPipelinesStub:
        async def execute(self, _environment_id):
            return [
                PipelineSummaryDTO(
                    id=pipeline_id,
                    environment_id=env_id,
                    name="deploy",
                    description="desc",
                )
            ]

    @dataclass
    class _GetPipelineStub:
        async def execute(self, _pipeline_id):
            return [
                PipelineOutputDTO(
                    id=step_id,
                    order=1,
                    name="pull",
                    step_type="ssh_command",
                    command="git pull",
                    on_failure="stop",
                    timeout_seconds=120,
                    working_directory="/srv/app",
                    is_active=True,
                )
            ]

    @dataclass
    class _UpdatePipelineStub:
        async def execute(self, _pipeline_id, _dto):
            return PipelineSummaryDTO(
                id=pipeline_id,
                environment_id=env_id,
                name="deploy-v2",
                description="desc",
            )

    @dataclass
    class _DeletePipelineStub:
        async def execute(self, _pipeline_id):
            return None

    @dataclass
    class _AddStepStub:
        async def execute(self, _dto):
            return PipelineOutputDTO(
                id=step_id,
                order=1,
                name="pull",
                step_type="ssh_command",
                command="git pull",
                on_failure="stop",
                timeout_seconds=120,
                working_directory="/srv/app",
                is_active=True,
            )

    @dataclass
    class _UpdateStepStub:
        async def execute(self, _pipeline_id, _step_id, _dto):
            return PipelineOutputDTO(
                id=step_id,
                order=1,
                name="pull-updated",
                step_type="ssh_command",
                command="git pull --rebase",
                on_failure="stop",
                timeout_seconds=180,
                working_directory="/srv/app",
                is_active=True,
            )

    @dataclass
    class _DeleteStepStub:
        async def execute(self, _pipeline_id, _step_id):
            return None

    @dataclass
    class _ReorderStepsStub:
        async def execute(self, _dto):
            return [
                PipelineOutputDTO(
                    id=step_id,
                    order=1,
                    name="pull",
                    step_type="ssh_command",
                    command="git pull",
                    on_failure="stop",
                    timeout_seconds=120,
                    working_directory="/srv/app",
                    is_active=True,
                )
            ]

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        sub=str(uuid4()), role="admin"
    )
    app.dependency_overrides[get_create_pipeline_use_case] = lambda: (
        _CreatePipelineStub()
    )
    app.dependency_overrides[get_list_pipelines_use_case] = lambda: _ListPipelinesStub()
    app.dependency_overrides[get_get_pipeline_use_case] = lambda: _GetPipelineStub()
    app.dependency_overrides[get_update_pipeline_use_case] = lambda: (
        _UpdatePipelineStub()
    )
    app.dependency_overrides[get_delete_pipeline_use_case] = lambda: (
        _DeletePipelineStub()
    )
    app.dependency_overrides[get_add_step_use_case] = lambda: _AddStepStub()
    app.dependency_overrides[get_update_step_use_case] = lambda: _UpdateStepStub()
    app.dependency_overrides[get_delete_step_use_case] = lambda: _DeleteStepStub()
    app.dependency_overrides[get_reorder_steps_use_case] = lambda: _ReorderStepsStub()

    with TestClient(app) as client:
        assert (
            client.get(
                f"/api/environments/{env_id}/pipelines",
                headers={"Authorization": "Bearer token"},
            ).status_code
            == 200
        )

        assert (
            client.post(
                f"/api/environments/{env_id}/pipelines",
                headers={"Authorization": "Bearer token"},
                json={"name": "deploy", "description": "desc"},
            ).status_code
            == 201
        )

        assert (
            client.get(
                f"/api/pipelines/{pipeline_id}",
                headers={"Authorization": "Bearer token"},
            ).status_code
            == 200
        )

        assert (
            client.put(
                f"/api/pipelines/{pipeline_id}",
                headers={"Authorization": "Bearer token"},
                json={"name": "deploy-v2", "description": "desc"},
            ).status_code
            == 200
        )

        assert (
            client.post(
                f"/api/pipelines/{pipeline_id}/steps",
                headers={"Authorization": "Bearer token"},
                json={
                    "order": 1,
                    "name": "pull",
                    "step_type": "ssh_command",
                    "command": "git pull",
                    "on_failure": "stop",
                    "timeout_seconds": 120,
                    "working_directory": "/srv/app",
                },
            ).status_code
            == 201
        )

        assert (
            client.put(
                f"/api/pipelines/{pipeline_id}/steps/{step_id}",
                headers={"Authorization": "Bearer token"},
                json={
                    "name": "pull-updated",
                    "step_type": "ssh_command",
                    "command": "git pull --rebase",
                    "on_failure": "stop",
                    "timeout_seconds": 180,
                    "working_directory": "/srv/app",
                    "is_active": True,
                },
            ).status_code
            == 200
        )

        assert (
            client.post(
                f"/api/pipelines/{pipeline_id}/steps/reorder",
                headers={"Authorization": "Bearer token"},
                json={"ordered_step_ids": [str(step_id)]},
            ).status_code
            == 200
        )

        assert (
            client.delete(
                f"/api/pipelines/{pipeline_id}/steps/{step_id}",
                headers={"Authorization": "Bearer token"},
            ).status_code
            == 204
        )

        assert (
            client.delete(
                f"/api/pipelines/{pipeline_id}",
                headers={"Authorization": "Bearer token"},
            ).status_code
            == 204
        )

    app.dependency_overrides.clear()
