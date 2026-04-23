from __future__ import annotations

from src.domain.entities.environment import Environment
from src.domain.value_objects.environment_type import EnvironmentType
from src.infrastructure.persistence.models.environment_model import EnvironmentModel


def environment_model_to_entity(row: EnvironmentModel) -> Environment:
    return Environment(
        id=row.id,
        project_id=row.project_id,
        name=row.name,
        environment_type=EnvironmentType(
            row.type.value if hasattr(row.type, "value") else str(row.type)
        ),
        server_id=row.server_id,
        working_directory=row.working_directory,
        is_active=row.is_active,
    )
