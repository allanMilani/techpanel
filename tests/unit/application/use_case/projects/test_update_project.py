from uuid import uuid4

import pytest

from src.application import NotFoundAppError
from src.application.use_cases.projects.update_project import UpdateProject
from tests.unit.application.fakes import MemoryProjectRepo
from src.domain.entities.project import Project
from src.application.dtos.project_dto import UpdateProjectInputDTO


@pytest.mark.asyncio
async def test_update_project_found() -> None:
    repo = MemoryProjectRepo()
    p = await repo.create(
        Project.create(
            name="x",
            repo_github="https://github.com/o/x",
            tech_stack="rs",
            created_by=str(uuid4()),
        )
    )
    uc = UpdateProject(repo)
    out = await uc.execute(
        p.id,
        UpdateProjectInputDTO(
            name="y",
            repo_github="https://github.com/o/y",
            tech_stack="js",
        ),
    )
    assert out.id == p.id
    assert out.name == "y"
    assert out.repo_github == "https://github.com/o/y"
    assert out.tech_stack == "js"


@pytest.mark.asyncio
async def test_update_project_not_found() -> None:
    repo = MemoryProjectRepo()
    uc = UpdateProject(repo)
    with pytest.raises(NotFoundAppError):
        await uc.execute(
            uuid4(),
            UpdateProjectInputDTO(
                name="y",
                repo_github="https://github.com/o/y",
                tech_stack="js",
            ),
        )
