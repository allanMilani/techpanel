import pytest
from uuid import uuid4

from src.application.dtos import (
    AddStepInputDTO,
    CreatePipelineInputDTO,
    CreateProjectInputDTO,
    CreateServerInputDTO,
    LinkEnvironmentInputDTO,
    LoginInputDTO,
    RunNextStepInputDTO,
    StartExecutionInputDTO,
)
from src.application.use_cases.auth.login import Login
from src.application.use_cases.executions.get_execution_logs import GetExecutionLogs
from src.application.use_cases.executions.get_history import GetHistory
from src.application.use_cases.executions.run_next_step import RunNextStep
from src.application.use_cases.executions.start_execution import StartExecution
from src.application.use_cases.pipelines.add_step import AddStep
from src.application.use_cases.pipelines.create_pipeline import CreatePipeline
from src.application.use_cases.projects.create_project import CreateProject
from src.application.use_cases.projects.link_environment import LinkEnvironment
from src.application.use_cases.servers.create_server import CreateServer
from src.domain.entities import Pipeline, User
from src.domain.value_objects.execution_status import ExecutionStatus
from src.domain.value_objects.on_failure_policy import OnFailurePolicy
from src.domain.value_objects.step_execution_status import StepExecutionStatus
from src.domain.value_objects.user_role import UserRole
from tests.unit.application.fakes import (
    FakeKeyCipher,
    FakeNotificationService,
    FakePasswordHasher,
    FakeRunnerRegistry,
    FakeTokenService,
    MemoryEnvironmentRepo,
    MemoryExecutionRepo,
    MemoryPipelineRepo,
    MemoryProjectRepo,
    MemoryServerRepo,
    MemoryStepExecutionRepo,
)


class MemoryUserRepo:
    def __init__(self) -> None:
        self.items: dict[str, User] = {}

    async def create(self, user: User) -> User:
        self.items[user.email] = user
        return user

    async def get_by_id(self, user_id):
        return next((u for u in self.items.values() if u.id == user_id), None)

    async def get_by_email(self, email: str) -> User | None:
        return self.items.get(email)


@pytest.mark.asyncio
async def test_integration_deploy_flow_with_fakes() -> None:
    user_repo = MemoryUserRepo()
    server_repo = MemoryServerRepo()
    project_repo = MemoryProjectRepo()
    environment_repo = MemoryEnvironmentRepo()
    pipeline_repo = MemoryPipelineRepo()
    execution_repo = MemoryExecutionRepo()
    step_execution_repo = MemoryStepExecutionRepo()

    admin = await user_repo.create(
        User.create(
            email="admin@techpanel.local",
            password_hash="hash",
            role=UserRole.ADMIN,
        )
    )
    login_out = await Login(
        user_repo=user_repo,
        password_hasher=FakePasswordHasher("secret"),
        token_service=FakeTokenService(),
    ).execute(LoginInputDTO(email=admin.email, password="secret"))
    assert login_out.user_id == admin.id

    server_out = await CreateServer(server_repo, FakeKeyCipher()).execute(
        CreateServerInputDTO(
            name="server-app",
            host="10.0.0.1",
            port=22,
            ssh_user="ubuntu",
            private_key_plain="PRIVATE_KEY",
            created_by=admin.id,
        )
    )
    project_out = await CreateProject(project_repo).execute(
        CreateProjectInputDTO(
            name="TechPanel",
            repo_github="org/techpanel",
            tech_stack="python",
            created_by=admin.id,
        )
    )
    env = await LinkEnvironment(project_repo, server_repo, environment_repo).execute(
        LinkEnvironmentInputDTO(
            project_id=project_out.id,
            name="staging",
            environment_type="staging",
            server_id=server_out.id,
            working_directory="/var/www/app",
        )
    )
    pipeline_out = await CreatePipeline(pipeline_repo).execute(
        CreatePipelineInputDTO(
            environment_id=env.id,
            name="deploy",
            description="flow",
            created_by=admin.id,
        )
    )
    await AddStep(pipeline_repo).execute(
        AddStepInputDTO(
            pipeline_id=pipeline_out.id,
            order=1,
            name="pull",
            step_type="ssh_command",
            command="git pull",
            on_failure=OnFailurePolicy.STOP.value,
        )
    )
    await AddStep(pipeline_repo).execute(
        AddStepInputDTO(
            pipeline_id=pipeline_out.id,
            order=2,
            name="health",
            step_type="http_healthcheck",
            command="https://example.com/health",
            on_failure=OnFailurePolicy.CONTINUE.value,
        )
    )

    started = await StartExecution(
        pipeline_repo=pipeline_repo,
        execution_repo=execution_repo,
        step_execution_repo=step_execution_repo,
    ).execute(
        StartExecutionInputDTO(
            pipeline_id=pipeline_out.id,
            triggered_by=admin.id,
            branch_or_tag="main",
        )
    )

    await RunNextStep(
        execution_repo=execution_repo,
        step_execution_repo=step_execution_repo,
        pipeline_repo=pipeline_repo,
        runner_registry=FakeRunnerRegistry(exit_code=0),
    ).execute(RunNextStepInputDTO(execution_id=started.id))

    logs = await GetExecutionLogs(execution_repo, step_execution_repo).execute(
        started.id
    )
    history = await GetHistory(execution_repo).execute(pipeline_out.id)
    final_execution = await execution_repo.get_by_id(started.id)

    assert len(logs) == 2
    assert {log.status for log in logs} == {StepExecutionStatus.SUCCESS.value}
    assert len(history) == 1
    assert final_execution is not None
    assert final_execution.status == ExecutionStatus.SUCCESS


@pytest.mark.asyncio
async def test_integration_notify_and_stop_with_fakes() -> None:
    user_repo = MemoryUserRepo()
    pipeline_repo = MemoryPipelineRepo()
    execution_repo = MemoryExecutionRepo()
    step_execution_repo = MemoryStepExecutionRepo()
    notification_service = FakeNotificationService()

    admin = await user_repo.create(
        User.create(
            email="ops@techpanel.local",
            password_hash="hash",
            role=UserRole.ADMIN,
        )
    )
    pipeline = await pipeline_repo.create(
        Pipeline.create(name="deploy", environment_id=str(uuid4()), description=None)
    )
    await AddStep(pipeline_repo).execute(
        AddStepInputDTO(
            pipeline_id=pipeline.id,
            order=1,
            name="failing-step",
            step_type="ssh_command",
            command="exit 1",
            on_failure=OnFailurePolicy.NOTIFY_AND_STOP.value,
        )
    )
    started = await StartExecution(
        pipeline_repo=pipeline_repo,
        execution_repo=execution_repo,
        step_execution_repo=step_execution_repo,
    ).execute(
        StartExecutionInputDTO(
            pipeline_id=pipeline.id,
            triggered_by=admin.id,
            branch_or_tag="main",
        )
    )
    await RunNextStep(
        execution_repo=execution_repo,
        step_execution_repo=step_execution_repo,
        pipeline_repo=pipeline_repo,
        runner_registry=FakeRunnerRegistry(exit_code=1),
        notification_service=notification_service,
    ).execute(RunNextStepInputDTO(execution_id=started.id))

    final_execution = await execution_repo.get_by_id(started.id)
    assert final_execution is not None
    assert final_execution.status == ExecutionStatus.FAILED
    assert len(notification_service.calls) == 1
