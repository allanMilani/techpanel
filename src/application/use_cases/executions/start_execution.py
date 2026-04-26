from src.application import ConflictAppError, NotFoundAppError
from src.application.dtos import ExecutionOutputDTO, StartExecutionInputDTO
from src.application.dtos.execution_dto import execution_to_output_dto
from src.domain.entities import Execution, StepExecution
from src.domain.ports.repositories import (
    IEnvironmentRepository,
    IExecutionRepository,
    IPipelineRepository,
    IStepExecutionRepository,
)


class StartExecution:
    def __init__(
        self,
        pipeline_repo: IPipelineRepository,
        environment_repo: IEnvironmentRepository,
        execution_repo: IExecutionRepository,
        step_execution_repo: IStepExecutionRepository,
    ) -> None:
        self.pipeline_repo = pipeline_repo
        self.environment_repo = environment_repo
        self.execution_repo = execution_repo
        self.step_execution_repo = step_execution_repo

    async def execute(self, dto: StartExecutionInputDTO) -> ExecutionOutputDTO:
        pipeline = await self.pipeline_repo.get_by_id(dto.pipeline_id)
        if pipeline is None:
            raise NotFoundAppError("Pipeline not found")

        environments = await self.environment_repo.list_by_pipeline(dto.pipeline_id)
        environment = next((e for e in environments if e.id == pipeline.environment_id), None)
        if environment is None:
            raise NotFoundAppError("Environment not found for pipeline")

        active = await self.execution_repo.get_active_execution_for_project(environment.project_id)
        if active is not None:
            raise ConflictAppError("Execution already running for this project")

        execution = Execution.create(
            pipeline_id=str(dto.pipeline_id),
            triggered_by=str(dto.triggered_by),
            branch_or_tag=dto.branch_or_tag,
        )

        created = await self.execution_repo.create(execution)
        steps = await self.pipeline_repo.list_steps(dto.pipeline_id)

        step_executions = [
            StepExecution.create(
                execution_id=str(created.id),
                pipeline_step_id=str(step.id),
                order=step.order,
            )
            for step in steps
            if step.is_active
        ]
        if step_executions:
            await self.step_execution_repo.create_many(step_executions)

        return execution_to_output_dto(created)