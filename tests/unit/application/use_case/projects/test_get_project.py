from uuid import uuid4

import pytest

from src.application import NotFoundAppError
from src.application.use_cases.projects.get_project import GetProject
from tests.unit.application.fakes import MemoryProjectRepo
from src.domain.entities.project import Project


@pytest.mark.asyncio
async def test_get_project_found() -> None:
    repo = MemoryProjectRepo()
    p = await repo.create(
        Project.create(
            name="x",
            repo_github="https://github.com/o/x",
            tech_stack="rs",
            created_by=str(uuid4()),
        )
    )
    uc = GetProject(repo)
    out = await uc.execute(p.id)
    assert out.id == p.id
    assert out.name == "x"


@pytest.mark.asyncio
async def test_get_project_not_found() -> None:
    repo = MemoryProjectRepo()
    uc = GetProject(repo)
    with pytest.raises(NotFoundAppError):
        await uc.execute(uuid4())
