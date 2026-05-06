from uuid import uuid4

import pytest

from src.application.use_cases.projects.list_projects import ListProjects
from tests.unit.application.fakes import MemoryProjectRepo
from src.domain.entities.project import Project


@pytest.mark.asyncio
async def test_list_projects_returns_all() -> None:
    repo = MemoryProjectRepo()
    await repo.create(
        Project.create(
            name="a",
            repo_github="https://github.com/o/a",
            tech_stack="py",
            created_by=str(uuid4()),
        )
    )
    await repo.create(
        Project.create(
            name="b",
            repo_github="https://github.com/o/b",
            tech_stack="go",
            created_by=str(uuid4()),
        )
    )
    uc = ListProjects(repo)
    out = await uc.execute(page=1, per_page=20)
    assert out.total == 2
    assert len(out.items) == 2
