from uuid import UUID

from dataclasses import replace

from src.application.dtos import (
    AddStepInputDTO,
    CreatePipelineInputDTO,
    CreateProjectInputDTO,
    CreateServerInputDTO,
    ExecutionOutputDTO,
    LinkEnvironmentInputDTO,
    LoginInputDTO,
    LoginOutputDTO,
    RunNextStepInputDTO,
    StartExecutionInputDTO,
)
from src.application.dtos.execution_dto import (
    execution_to_output_dto,
    step_execution_to_output_dto,
)
from src.application.dtos.pipeline_dto import (
    pipeline_step_to_output_dto,
    pipeline_to_summary_dto,
)
from src.domain.entities.execution import Execution
from src.domain.entities.pipeline import Pipeline
from src.domain.entities.pipeline_step import PipelineStep
from src.domain.entities.step_execution import StepExecution
from src.domain.value_objects.on_failure_policy import OnFailurePolicy
from src.domain.value_objects.step_execution_status import StepExecutionStatus
from src.domain.value_objects.step_type import StepType


def test_login_dtos_immutability() -> None:
    dto = LoginInputDTO(email="a@b.com", password="x")
    assert dto.email == "a@b.com"
    out = LoginOutputDTO(
        access_token="t",
        token_type="Bearer",
        user_id=UUID("00000000-0000-0000-0000-000000000001"),
        role="admin",
        display_name="Admin",
        has_github_token=False,
    )
    assert out.token_type == "Bearer"


def test_add_step_dto_defaults() -> None:
    dto = AddStepInputDTO(
        pipeline_id=UUID("00000000-0000-0000-0000-000000000001"),
        name="s",
        step_type="ssh_command",
        command="echo",
        on_failure="stop",
        order=1,
    )
    assert dto.timeout_seconds == 300
    assert dto.working_directory is None
    assert dto.order == 1

    auto_order = AddStepInputDTO(
        pipeline_id=UUID("00000000-0000-0000-0000-000000000001"),
        name="t",
        step_type="ssh_command",
        command="x",
        on_failure="stop",
    )
    assert auto_order.order is None


def test_create_pipeline_input_has_created_by() -> None:
    dto = CreatePipelineInputDTO(
        environment_id=UUID("00000000-0000-0000-0000-000000000002"),
        name="Deploy",
        description=None,
        created_by=UUID("00000000-0000-0000-0000-000000000003"),
    )
    assert dto.created_by == UUID("00000000-0000-0000-0000-000000000003")


def test_link_environment_dto() -> None:
    dto = LinkEnvironmentInputDTO(
        project_id=UUID("00000000-0000-0000-0000-000000000001"),
        name="staging",
        environment_type="staging",
        server_id=UUID("00000000-0000-0000-0000-000000000002"),
        working_directory="/app",
    )
    assert dto.environment_type == "staging"


def test_create_server_dto() -> None:
    dto = CreateServerInputDTO(
        name="srv",
        host="127.0.0.1",
        port=22,
        ssh_user="u",
        private_key_plain="k",
        created_by=UUID("00000000-0000-0000-0000-000000000001"),
    )
    assert dto.port == 22


def test_create_project_dto() -> None:
    dto = CreateProjectInputDTO(
        name="p",
        repo_github="o/r",
        tech_stack="python",
        created_by=UUID("00000000-0000-0000-0000-000000000001"),
    )
    assert dto.repo_github == "o/r"


def test_execution_dtos_and_mappers() -> None:
    e = Execution.create(
        pipeline_id="00000000-0000-0000-0000-000000000001",
        triggered_by="00000000-0000-0000-0000-000000000002",
        branch_or_tag="main",
    )
    out = execution_to_output_dto(e)
    assert isinstance(out, ExecutionOutputDTO)
    assert out.status == "pending"
    assert out.created_at == e.created_at

    se = StepExecution.create(
        execution_id=str(e.id),
        pipeline_step_id="00000000-0000-0000-0000-000000000003",
        order=1,
    )
    seo = step_execution_to_output_dto(se)
    assert seo.status == StepExecutionStatus.PENDING.value
    assert seo.pipeline_step_id == UUID("00000000-0000-0000-0000-000000000003")

    se_orphan = replace(se, pipeline_step_id=None)
    seo2 = step_execution_to_output_dto(se_orphan)
    assert seo2.pipeline_step_id is None


def test_pipeline_mappers() -> None:
    p = Pipeline.create("n", "00000000-0000-0000-0000-000000000001")
    summary = pipeline_to_summary_dto(p)
    assert summary.name == "n"

    step = PipelineStep.create(
        pipeline_id=str(p.id),
        order=1,
        name="s",
        step_type=StepType.SSH_COMMAND,
        command="c",
        on_failure=OnFailurePolicy.STOP,
    )
    pod = pipeline_step_to_output_dto(step)
    assert pod.step_type == "ssh_command"
    assert pod.is_active is True


def test_start_and_run_next_step_dtos() -> None:
    s = StartExecutionInputDTO(
        pipeline_id=UUID("00000000-0000-0000-0000-000000000001"),
        triggered_by=UUID("00000000-0000-0000-0000-000000000002"),
        branch_or_tag="main",
        triggered_by_ip="127.0.0.1",
    )
    assert s.triggered_by_ip == "127.0.0.1"

    r = RunNextStepInputDTO(execution_id=UUID("00000000-0000-0000-0000-000000000099"))
    assert r.execution_id == UUID("00000000-0000-0000-0000-000000000099")
