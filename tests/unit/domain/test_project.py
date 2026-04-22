import pytest

from src.domain.entities.project import Project
from src.domain.errors import ValidationError


def test_deve_criar_projeto_valido() -> None:
    project = Project.create(
        name="TechPanel",
        repo_github="allan/techpanel",
        tech_stack="python",
        created_by="00000000-0000-0000-0000-000000000001",
    )
    assert project.repo_github == "allan/techpanel"


def test_deve_falhar_com_repo_invalido() -> None:
    with pytest.raises(ValidationError):
        Project.create(
            name="TechPanel",
            repo_github="invalido",
            tech_stack="python",
            created_by="00000000-0000-0000-0000-000000000001",
        )