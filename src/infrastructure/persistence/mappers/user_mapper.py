from __future__ import annotations

from src.domain.entities import User
from src.domain.value_objects.user_role import UserRole
from src.infrastructure.persistence.models.user_model import UserModel


def user_model_to_entity(row: UserModel) -> User:
    return User(
        id=row.id,
        email=row.email,
        password_hash=row.password_hash,
        role=UserRole(row.role.value if hasattr(row.role, "value") else str(row.role)),
        is_active=row.is_active,
        display_name=row.display_name,
        github_token_enc=row.github_token_enc,
    )


def apply_user_entity_to_model(user: User, target: UserModel) -> None:
    target.email = user.email
    target.password_hash = user.password_hash
    target.role = user.role.value if hasattr(user.role, "value") else str(user.role)
    target.is_active = user.is_active
    target.display_name = user.display_name
    target.github_token_enc = user.github_token_enc
