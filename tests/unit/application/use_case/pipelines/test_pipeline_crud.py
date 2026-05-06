from uuid import uuid4

import pytest

from src.application import NotFoundAppError
from src.application.dtos import CreatePipelineInputDTO, UpdatePipelineInputDTO
from src.application.use_cases.pipelines.create_pipeline import CreatePipeline
from src.application.use_cases.pipelines.delete_pipeline import DeletePipeline
from src.application.use_cases.pipelines.get_pipeline import GetPipeline
from src.application.use_cases.pipelines.list_pipelines import ListPipelines
from src.application.use_cases.pipelines.update_pipeline import UpdatePipeline
from tests.unit.application.fakes import MemoryPipelineRepo


@pytest.mark.asyncio
async def test_pipeline_crud_flow() -> None:
    repo = MemoryPipelineRepo()
    create_uc = CreatePipeline(repo)

    created = await create_uc.execute(
        CreatePipelineInputDTO(
            environment_id=uuid4(),
            name="deploy-app",
            description="pipeline principal",
            created_by=uuid4(),
        )
    )

    list_uc = ListPipelines(repo)
    listed = await list_uc.execute(created.environment_id, page=1, per_page=20)
    assert listed.total == 1
    assert len(listed.items) == 1
    assert listed.items[0].id == created.id

    update_uc = UpdatePipeline(repo)
    updated = await update_uc.execute(
        created.id,
        UpdatePipelineInputDTO(name="deploy-app-v2", description="atualizada"),
    )
    assert updated.name == "deploy-app-v2"

    delete_uc = DeletePipeline(repo)
    await delete_uc.execute(created.id)

    with pytest.raises(NotFoundAppError):
        await delete_uc.execute(created.id)


@pytest.mark.asyncio
async def test_get_pipeline_not_found() -> None:
    repo = MemoryPipelineRepo()
    use_case = GetPipeline(repo)

    with pytest.raises(NotFoundAppError):
        await use_case.execute(uuid4(), page=1, per_page=20)
