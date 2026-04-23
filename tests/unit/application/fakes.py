from uuid import UUID

from src.domain.entities.environment import Environment
from src.domain.entities.execution import Execution
from src.domain.entities.pipeline import Pipeline
from src.domain.entities.pipeline_step import PipelineStep
from src.domain.entities.project import Project
from src.domain.entities.server import Server
from src.domain.entities.step_execution import StepExecution
from src.domain.value_objects.step_type import StepType


class FakePasswordHasher:
    def __init__(self, valid_password: str = "secret") -> None:
        self.valid_password = valid_password

    def verify(self, raw: str, hashed: str) -> bool:
        _ = hashed
        return raw == self.valid_password


class FakeTokenService:
    def create_access_token(self, sub: str, role: str) -> str:
        return f"token.{sub}.{role}"


class FakeKeyCipher:
    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    def encrypt(self, plain: str) -> str:
        token = f"enc:{plain}"
        self._store[token] = plain
        return token

    def decrypt(self, enc: str) -> str:
        return self._store.get(enc, enc.replace("enc:", ""))


class FakeSSHService:
    def __init__(self, result: bool = True) -> None:
        self.result = result

    async def test_connection(
        self, host: str, port: int, username: str, private_key: str
    ) -> bool:
        return self.result

    async def execute(
        self,
        host: str,
        port: int,
        username: str,
        private_key: str,
        command: str,
        cwd: str | None = None,
    ) -> tuple[int, str]:
        return 0, "ok"


class FakeRunner:
    def __init__(self, exit_code: int = 0, log: str = "ok") -> None:
        self.exit_code = exit_code
        self.log = log

    async def run(self, step: PipelineStep) -> tuple[int, str]:
        return self.exit_code, self.log


class FakeRunnerRegistry:
    def __init__(self, exit_code: int = 0) -> None:
        self.exit_code = exit_code

    def get(self, step_type: StepType) -> FakeRunner:
        return FakeRunner(self.exit_code)


class FakeNotificationService:
    def __init__(self) -> None:
        self.calls: list[tuple[Execution, StepExecution | None]] = []

    async def notify_execution_failed(
        self,
        execution: Execution,
        failed_step: StepExecution | None,
    ) -> None:
        self.calls.append((execution, failed_step))


class MemoryExecutionRepo:
    def __init__(self) -> None:
        self.items: dict[UUID, Execution] = {}
        self.active_by_env: dict[UUID, Execution] = {}

    async def create(self, execution: Execution) -> Execution:
        self.items[execution.id] = execution
        return execution

    async def update(self, execution: Execution) -> Execution:
        self.items[execution.id] = execution
        return execution

    async def get_by_id(self, execution_id: UUID) -> Execution | None:
        return self.items.get(execution_id)

    async def list_by_pipeline(self, pipeline_id: UUID) -> list[Execution]:
        return [e for e in self.items.values() if e.pipeline_id == pipeline_id]

    async def get_active_execution_for_environment(
        self, environment_id: UUID
    ) -> Execution | None:
        return self.active_by_env.get(environment_id)

    def set_active_for_env(
        self, environment_id: UUID, execution: Execution | None
    ) -> None:
        if execution is None:
            self.active_by_env.pop(environment_id, None)
        else:
            self.active_by_env[environment_id] = execution


class MemoryStepExecutionRepo:
    def __init__(self) -> None:
        self.items: dict[UUID, StepExecution] = {}

    async def create_many(self, steps: list[StepExecution]) -> list[StepExecution]:
        for s in steps:
            self.items[s.id] = s
        return steps

    async def update(self, step_execution: StepExecution) -> StepExecution:
        self.items[step_execution.id] = step_execution
        return step_execution

    async def get_by_id(self, step_execution_id: UUID) -> StepExecution | None:
        return self.items.get(step_execution_id)

    async def get_last_by_execution(self, execution_id: UUID) -> StepExecution | None:
        exec_steps = [s for s in self.items.values() if s.execution_id == execution_id]
        if not exec_steps:
            return None
        return max(exec_steps, key=lambda s: s.order)

    async def list_by_execution(self, execution_id: UUID) -> list[StepExecution]:
        return sorted(
            (s for s in self.items.values() if s.execution_id == execution_id),
            key=lambda s: s.order,
        )

    async def skip_remaining(self, execution_id: UUID, after_order: int) -> None:
        for s in self.items.values():
            if s.execution_id == execution_id and s.order > after_order:
                self.items[s.id] = s.mark_skipped("skipped")


class MemoryServerRepo:
    def __init__(self) -> None:
        self.items: dict[UUID, Server] = {}

    async def create(self, server: Server) -> Server:
        self.items[server.id] = server
        return server

    async def update(self, server: Server) -> Server:
        self.items[server.id] = server
        return server

    async def get_by_id(self, server_id: UUID) -> Server | None:
        return self.items.get(server_id)

    async def list_all(self) -> list[Server]:
        return list(self.items.values())

    async def delete(self, server_id: UUID) -> None:
        self.items.pop(server_id, None)


class MemoryProjectRepo:
    def __init__(self) -> None:
        self.items: dict[UUID, Project] = {}

    async def create(self, project: Project) -> Project:
        self.items[project.id] = project
        return project

    async def update(self, project: Project) -> Project:
        self.items[project.id] = project
        return project

    async def get_by_id(self, project_id: UUID) -> Project | None:
        return self.items.get(project_id)

    async def list_all(self) -> list[Project]:
        return list(self.items.values())

    async def delete(self, project_id: UUID) -> None:
        self.items.pop(project_id, None)


class MemoryEnvironmentRepo:
    def __init__(self) -> None:
        self.items: dict[UUID, Environment] = {}

    async def create(self, environment: Environment) -> Environment:
        self.items[environment.id] = environment
        return environment

    async def update(self, environment: Environment) -> Environment:
        self.items[environment.id] = environment
        return environment

    async def get_by_id(self, environment_id: UUID) -> Environment | None:
        return self.items.get(environment_id)

    async def list_by_pipeline(self, pipeline_id: UUID) -> list[Environment]:
        return []

    async def get_active_by_project(self, project_id: UUID) -> Environment | None:
        return None


class MemoryPipelineRepo:
    def __init__(
        self,
        pipeline: Pipeline | None = None,
        steps: list[PipelineStep] | None = None,
    ) -> None:
        self.pipelines: dict[UUID, Pipeline] = {}
        self.steps: dict[UUID, list[PipelineStep]] = {}
        if pipeline is not None:
            self.pipelines[pipeline.id] = pipeline
            self.steps[pipeline.id] = list(steps if steps is not None else [])

    async def create(self, pipeline: Pipeline) -> Pipeline:
        self.pipelines[pipeline.id] = pipeline
        self.steps.setdefault(pipeline.id, [])
        return pipeline

    async def update(self, pipeline: Pipeline) -> Pipeline:
        self.pipelines[pipeline.id] = pipeline
        return pipeline

    async def get_by_id(self, pipeline_id: UUID) -> Pipeline | None:
        return self.pipelines.get(pipeline_id)

    async def list_by_environment(self, environment_id: UUID) -> list[Pipeline]:
        return [
            p for p in self.pipelines.values() if p.environment_id == environment_id
        ]

    async def delete(self, pipeline_id: UUID) -> None:
        self.pipelines.pop(pipeline_id, None)
        self.steps.pop(pipeline_id, None)

    async def add_step(self, step: PipelineStep) -> PipelineStep:
        self.steps.setdefault(step.pipeline_id, []).append(step)
        return step

    async def update_step(self, step: PipelineStep) -> PipelineStep:
        lst = self.steps[step.pipeline_id]
        self.steps[step.pipeline_id] = [s if s.id != step.id else step for s in lst]
        return step

    async def remove_step(self, step_id: UUID) -> None:
        for pid, lst in self.steps.items():
            self.steps[pid] = [s for s in lst if s.id != step_id]

    async def list_steps(self, pipeline_id: UUID) -> list[PipelineStep]:
        return sorted(self.steps.get(pipeline_id, []), key=lambda s: s.order)

    async def get_next_step(
        self, pipeline_id: UUID, after_order: int
    ) -> PipelineStep | None:
        ordered = await self.list_steps(pipeline_id)
        for s in ordered:
            if s.order > after_order and s.is_active:
                return s
        return None
