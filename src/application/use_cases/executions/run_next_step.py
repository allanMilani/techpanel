from uuid import UUID

from src.application import NotFoundAppError, ValidationAppError
from src.application.dtos import RunNextStepInputDTO
from src.domain.entities.execution import Execution
from src.domain.entities.step_execution import StepExecution
from src.application.use_cases.executions.workspace_git_prepare import WorkspaceGitPrepare
from src.domain.ports.repositories import (
    IExecutionRepository,
    IPipelineRepository,
    IStepExecutionRepository,
)
from src.domain.ports.services import (
    IDockerExecService,
    INotificationService,
    IRunnerRegistry,
    ISSHService,
)
from src.domain.value_objects.execution_status import ExecutionStatus
from src.domain.value_objects.on_failure_policy import OnFailurePolicy
from src.domain.value_objects.step_execution_status import StepExecutionStatus


class RunNextStep:
    """Avança a execução em **no máximo um passo** de pipeline por `execute()`.

    O cliente (ex.: monitor da UI) deve chamar `POST /executions/{id}/next-step` em
    loop até o status da execução ser terminal (`success`, `failed`, `cancelled`, `blocked`).
    """

    def __init__(
        self,
        execution_repo: IExecutionRepository,
        step_execution_repo: IStepExecutionRepository,
        pipeline_repo: IPipelineRepository,
        runner_registry: IRunnerRegistry,
        workspace_git_prepare: WorkspaceGitPrepare,
        ssh_service: ISSHService,
        docker_exec: IDockerExecService,
        notification_service: INotificationService | None = None,
    ) -> None:
        self.execution_repo = execution_repo
        self.step_execution_repo = step_execution_repo
        self.pipeline_repo = pipeline_repo
        self.runner_registry = runner_registry
        self.workspace_git_prepare = workspace_git_prepare
        self.ssh_service = ssh_service
        self.docker_exec = docker_exec
        self.notification_service = notification_service

    async def _release_pipeline_remote_sessions(self, execution_id: UUID) -> None:
        await self.ssh_service.release_pipeline_session(execution_id)
        await self.docker_exec.release_pipeline_session(execution_id)

    async def _pending_step_execution(self, execution_id: UUID, pipeline_step_id: UUID):
        steps = await self.step_execution_repo.list_by_execution(execution_id)
        return next(
            (
                s
                for s in steps
                if s.pipeline_step_id == pipeline_step_id
                and s.status == StepExecutionStatus.PENDING
            ),
            None,
        )

    async def _apply_stop_or_notify_on_failed_last(
        self,
        execution: Execution,
        all_step_execs: list[StepExecution],
    ) -> bool:
        """Se o último passo em falha exige parar a pipeline, aplica e retorna True."""
        failed_last = next(
            (
                s
                for s in reversed(all_step_execs)
                if s.status == StepExecutionStatus.FAILED
            ),
            None,
        )
        if failed_last is None:
            return False

        pipeline_steps = await self.pipeline_repo.list_steps(execution.pipeline_id)
        failed_def = next(
            (s for s in pipeline_steps if s.id == failed_last.pipeline_step_id),
            None,
        )
        if failed_def is None:
            # Passo removido da definição da pipeline ou referência órfã: aplica paragem segura.
            await self.step_execution_repo.skip_remaining(execution.id, failed_last.order)
            await self.execution_repo.update(execution.mark_failed())
            return True

        if failed_def.on_failure == OnFailurePolicy.STOP:
            await self.step_execution_repo.skip_remaining(execution.id, failed_last.order)
            await self.execution_repo.update(execution.mark_failed())
            return True

        if failed_def.on_failure == OnFailurePolicy.NOTIFY_AND_STOP:
            if self.notification_service is None:
                raise ValidationAppError(
                    "Notification service is required for NOTIFY_AND_STOP policy"
                )
            await self.notification_service.notify_execution_failed(execution, failed_last)
            await self.step_execution_repo.skip_remaining(execution.id, failed_last.order)
            await self.execution_repo.update(execution.mark_failed())
            return True

        return False

    async def execute(self, dto: RunNextStepInputDTO) -> None:
        execution = await self.execution_repo.get_by_id(dto.execution_id)
        if execution is None:
            raise NotFoundAppError("Execution not found")
        if execution.status == ExecutionStatus.CANCELLED:
            return
        if execution.status == ExecutionStatus.PENDING:
            execution = await self.execution_repo.update(execution.mark_running())

        all_step_execs = await self.step_execution_repo.list_by_execution(dto.execution_id)
        if await self._apply_stop_or_notify_on_failed_last(execution, all_step_execs):
            return

        terminal_orders = [
            s.order
            for s in all_step_execs
            if s.status
            in (
                StepExecutionStatus.SUCCESS,
                StepExecutionStatus.FAILED,
                StepExecutionStatus.SKIPPED,
            )
        ]
        after_order = max(terminal_orders, default=0)

        if execution.workspace_prepare_exit_code is None:
            pipeline = await self.pipeline_repo.get_by_id(execution.pipeline_id)
            if pipeline is None:
                raise NotFoundAppError("Pipeline not found")
            if pipeline.run_git_workspace_sync:
                prep_code, prep_log = await self.workspace_git_prepare.run(
                    pipeline=pipeline,
                    branch_or_tag=execution.branch_or_tag,
                )
            else:
                prep_log = "Sincronização Git desativada para esta pipeline.\n"
                prep_code = 0
            execution = execution.with_workspace_prepare(prep_log, prep_code)
            execution = await self.execution_repo.update(execution)
            if prep_code != 0:
                await self.step_execution_repo.skip_remaining(execution.id, 0)
                await self.execution_repo.update(execution.mark_failed())
                await self._release_pipeline_remote_sessions(execution.id)
                return

        next_step = await self.pipeline_repo.get_next_step(execution.pipeline_id, after_order)

        if next_step is None:
            await self._release_pipeline_remote_sessions(execution.id)
            await self.execution_repo.update(execution.mark_success())
            return

        pending = await self._pending_step_execution(execution.id, next_step.id)
        if pending is None:
            raise NotFoundAppError("Pending step execution not found for next pipeline step")

        running = pending.mark_running()
        await self.step_execution_repo.update(running)

        runner = self.runner_registry.get(next_step.step_type)
        exit_code, log_output = await runner.run(next_step, execution_id=execution.id)

        if exit_code == 0:
            await self.step_execution_repo.update(running.mark_success(log_output, exit_code))
            return

        await self.step_execution_repo.update(running.mark_failed(log_output, exit_code))
        all_after_fail = await self.step_execution_repo.list_by_execution(dto.execution_id)
        stopped = await self._apply_stop_or_notify_on_failed_last(execution, all_after_fail)
        if stopped:
            await self._release_pipeline_remote_sessions(execution.id)
