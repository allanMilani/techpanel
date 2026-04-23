import pytest

from src.domain.entities.user import User
from src.domain.errors import ValidationError
from src.domain.value_objects.user_role import UserRole


def test_should_create_user_successfully() -> None:
    user = User.create(
        email="test@example.com",
        password_hash="password",
        role=UserRole.ADMIN,
    )

    assert user.email == "test@example.com"
    assert user.is_active is True


def test_should_raise_validation_error_if_email_is_invalid() -> None:
    with pytest.raises(ValidationError):
        User.create(
            email="invalid-email",
            password_hash="x",
            role=UserRole.ADMIN,
        )
