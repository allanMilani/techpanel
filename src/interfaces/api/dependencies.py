from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.ports.repositories import IUserRepository
from src.application.use_cases.auth.login import Login
from src.infrastructure.persistence.repositories.pg_user_repository import (
    PgUserRepository,
)
from src.infrastructure.persistence.database import get_db_session


class PasswordHasherStub:
    def verify(self, raw: str, hashed: str) -> bool:
        _ = hashed
        return bool(raw)


class TokenServiceStub:
    def create_access_token(self, sub: str, role: str) -> str:
        return f"token.{sub}.{role}"


@dataclass(slots=True, frozen=True)
class CurrentUser:
    sub: str
    role: str


def get_user_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> IUserRepository:
    return PgUserRepository(session)


def get_login_use_case(
    user_repo: Annotated[IUserRepository, Depends(get_user_repository)],
) -> Login:
    return Login(
        user_repo=user_repo,
        password_hasher=PasswordHasherStub(),
        token_service=TokenServiceStub(),
    )


def get_current_user(
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> CurrentUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
        )

    token = authorization.removeprefix("Bearer ").strip()
    if token != "dev-admin-token":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    return CurrentUser(sub="dev-user", role="admin")


def require_admin(
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> CurrentUser:
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )

    return user
