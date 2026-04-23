from __future__ import annotations

from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import User
from src.domain.ports.repositories import IUserRepository
from src.infrastructure.persistence.models import UserModel
from src.infrastructure.persistence.mappers import user_model_to_entity


class PgUserRepository(IUserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, user: User) -> User:
        row = UserModel(
            id=user.id,
            email=user.email,
            password_hash=user.password_hash,
            role=user.role.value if hasattr(user.role, "value") else str(user.role),
            is_active=user.is_active,
        )

        self._session.add(row)
        await self._session.flush()
        return user_model_to_entity(row)

    async def get_by_id(self, id: UUID) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == id)
        )
        row = result.scalar_one_or_none()
        return user_model_to_entity(row) if row else None

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        row = result.scalar_one_or_none()
        return user_model_to_entity(row) if row else None
