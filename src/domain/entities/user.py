from dataclasses import dataclass
from uuid import UUID, uuid4

from src.domain.errors import ValidationError
from src.domain.value_objects.user_role import UserRole


@dataclass(slots=True, frozen=True)
class User:
    id: UUID
    email: str
    password_hash: str
    role: UserRole
    is_active: bool

    @staticmethod
    def create(email: str, password_hash: str, role: UserRole) -> "User":
        if not email:
            raise ValidationError("Email is required")

        if not password_hash:
            raise ValidationError("Password is required")

        if not role:
            raise ValidationError("Role is required")

        if "@" not in email:
            raise ValidationError("Invalid email")

        return User(
            id=uuid4(),
            email=email,
            password_hash=password_hash,
            role=role,
            is_active=True,
        )
