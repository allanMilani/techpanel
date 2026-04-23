from dataclasses import dataclass
from uuid import UUID, uuid4

from src.domain.errors import ValidationError


@dataclass(slots=True, frozen=True)
class Project:
    id: UUID
    name: str
    repo_github: str
    tech_stack: str
    created_by: UUID

    @staticmethod
    def create(
        name: str, repo_github: str, tech_stack: str, created_by: str
    ) -> "Project":
        if not name.strip():
            raise ValidationError("Name is required")

        if not repo_github.strip():
            raise ValidationError("Repo GitHub is required")

        if "/" not in repo_github:
            raise ValidationError("Repo GitHub must be in the format 'owner/repo'")

        if not tech_stack.strip():
            raise ValidationError("Tech stack is required")

        if not created_by.strip():
            raise ValidationError("Created by is required")

        return Project(
            id=uuid4(),
            name=name.strip(),
            repo_github=repo_github.strip(),
            tech_stack=tech_stack.strip().lower(),
            created_by=UUID(created_by),
        )
