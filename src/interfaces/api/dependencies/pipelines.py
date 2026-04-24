from typing import Annotated

from fastapi import Depends

from src.application.use_cases.pipelines.add_step import AddStep
from src.application.use_cases.pipelines.create_pipeline import CreatePipeline
from src.application.use_cases.pipelines.delete_pipeline import DeletePipeline
from src.application.use_cases.pipelines.delete_step import DeleteStep
from src.application.use_cases.pipelines.get_pipeline import GetPipeline
from src.application.use_cases.pipelines.list_pipelines import ListPipelines
from src.application.use_cases.pipelines.reorder_steps import ReorderSteps
from src.application.use_cases.pipelines.update_pipeline import UpdatePipeline
from src.application.use_cases.pipelines.update_step import UpdateStep
from src.domain.ports.repositories import IPipelineRepository
from src.interfaces.api.dependencies.core import get_pipeline_repository


def get_create_pipeline_use_case(
    pipeline_repo: Annotated[IPipelineRepository, Depends(get_pipeline_repository)],
) -> CreatePipeline:
    return CreatePipeline(pipeline_repo=pipeline_repo)


def get_list_pipelines_use_case(
    pipeline_repo: Annotated[IPipelineRepository, Depends(get_pipeline_repository)],
) -> ListPipelines:
    return ListPipelines(pipeline_repo=pipeline_repo)


def get_get_pipeline_use_case(
    pipeline_repo: Annotated[IPipelineRepository, Depends(get_pipeline_repository)],
) -> GetPipeline:
    return GetPipeline(pipeline_repo=pipeline_repo)


def get_update_pipeline_use_case(
    pipeline_repo: Annotated[IPipelineRepository, Depends(get_pipeline_repository)],
) -> UpdatePipeline:
    return UpdatePipeline(pipeline_repo=pipeline_repo)


def get_delete_pipeline_use_case(
    pipeline_repo: Annotated[IPipelineRepository, Depends(get_pipeline_repository)],
) -> DeletePipeline:
    return DeletePipeline(pipeline_repo=pipeline_repo)


def get_add_step_use_case(
    pipeline_repo: Annotated[IPipelineRepository, Depends(get_pipeline_repository)],
) -> AddStep:
    return AddStep(pipeline_repo=pipeline_repo)


def get_update_step_use_case(
    pipeline_repo: Annotated[IPipelineRepository, Depends(get_pipeline_repository)],
) -> UpdateStep:
    return UpdateStep(pipeline_repo=pipeline_repo)


def get_delete_step_use_case(
    pipeline_repo: Annotated[IPipelineRepository, Depends(get_pipeline_repository)],
) -> DeleteStep:
    return DeleteStep(pipeline_repo=pipeline_repo)


def get_reorder_steps_use_case(
    pipeline_repo: Annotated[IPipelineRepository, Depends(get_pipeline_repository)],
) -> ReorderSteps:
    return ReorderSteps(pipeline_repo=pipeline_repo)
