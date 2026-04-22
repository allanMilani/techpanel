import pytest

from src.domain.entities.environment import Environment
from src.domain.errors import ValidationError
from src.domain.value_objects.environment_type import EnvironmentType


def test_should_create_environment_successfully() -> None:
    env = Environment.create(
        project_id="00000000-0000-0000-0000-000000000001",
        name="production",
        environment_type=EnvironmentType.PRODUCTION,
        server_id="00000000-0000-0000-0000-000000000002",
        working_directory="/var/www/app",
    )
    assert env.is_active is True


def test_should_raise_validation_error_if_working_directory_is_relative() -> None:
    with pytest.raises(ValidationError):
        Environment.create(
            project_id="00000000-0000-0000-0000-000000000001",
            name="staging",
            environment_type=EnvironmentType.STAGING,
            server_id="00000000-0000-0000-0000-000000000002",
            working_directory="var/www/app",
        )