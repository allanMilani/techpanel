from __future__ import annotations

from src.domain.entities.project import Project
from src.infrastructure.persistence.models.project_model import ProjectModel


def project_model_to_entity(row: ProjectModel) -> Project:
    return Project(
        id=row.id,
        name=row.name,
        repo_github=row.repo_github,
        tech_stack=row.tech_stack,
        created_by=row.created_by,
    )
