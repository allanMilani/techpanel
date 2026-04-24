from uuid import uuid4

import pytest

from src.application import NotFoundAppError
from src.application.use_cases.projects.delete_project import DeleteProject
from tests.unit.application.fakes import MemoryProjectRepo
from src.domain.entities.project import Project


@pytest.mark.asyncio
async def test_delete_project_found() -> None:
    repo = MemoryProjectRepo()
    p = await repo.create(
        Project.create(
            name="x",
            repo_github="https://github.com/o/x",
            tech_stack="rs",
            created_by=str(uuid4()),
        )
    )
    uc = DeleteProject(repo)
    await uc.execute(p.id)
    assert await repo.get_by_id(p.id) is None


@pytest.mark.asyncio
async def test_delete_project_not_found() -> None:
    repo = MemoryProjectRepo()
    uc = DeleteProject(repo)
    with pytest.raises(NotFoundAppError):
        await uc.execute(uuid4())
