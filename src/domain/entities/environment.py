from dataclasses import dataclass
from uuid import UUID, uuid4

from src.domain.errors import ValidationError
from src.domain.value_objects.environment_type import EnvironmentType

@dataclass(slots=True, frozen=True)
class Environment:
    id: UUID
    project_id: UUID
    name: str
    environment_type: EnvironmentType
    server_id: UUID
    working_directory: str
    is_active: bool = True

    @staticmethod
    def create(
        project_id: str, 
        name: str, 
        environment_type: EnvironmentType, 
        server_id: str, 
        working_directory: str
    ) -> "Environment":
        if not project_id:
            raise ValidationError("Project ID is required")

        if not name.strip():
            raise ValidationError("Name is required")

        if not environment_type:
            raise ValidationError("Environment type is required")
        
        if not server_id:
            raise ValidationError("Server ID is required")

        if not working_directory.strip():
            raise ValidationError("Working directory is required")

        if not working_directory.startswith("/"):
            raise ValidationError("Working directory must start with a slash")

        return Environment(
            id=uuid4(),
            project_id=UUID(project_id),
            name=name.strip().lower(),
            environment_type=environment_type,
            server_id=UUID(server_id),
            working_directory=working_directory.strip(),
            is_active=True,
        )