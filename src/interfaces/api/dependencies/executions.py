from typing import Annotated

from fastapi import Depends

from src.application.use_cases.executions.start_execution import StartExecution
from src.domain.ports.repositories import (
    IExecutionRepository,
    IPipelineRepository,
    IStepExecutionRepository,
)
from src.interfaces.api.dependencies.core import (
    get_execution_repository,
    get_pipeline_repository,
    get_step_execution_repository,
)


def get_start_execution_use_case(
    pipeline_repo: Annotated[IPipelineRepository, Depends(get_pipeline_repository)],
    execution_repo: Annotated[IExecutionRepository, Depends(get_execution_repository)],
    step_execution_repo: Annotated[
        IStepExecutionRepository, Depends(get_step_execution_repository)
    ],
) -> StartExecution:
    return StartExecution(
        pipeline_repo=pipeline_repo,
        execution_repo=execution_repo,
        step_execution_repo=step_execution_repo,
    )
