from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.use_cases.auth.login import Login
from src.application.use_cases.executions.start_execution import StartExecution
from src.domain.ports.repositories import (
    IExecutionRepository,
    IPipelineRepository,
    IStepExecutionRepository,
    IUserRepository,
)
from src.domain.ports.services import IPasswordHasher, ITokenService
from src.infrastructure.persistence.repositories.pg_user_repository import (
    PgUserRepository,
)
from src.infrastructure.persistence.database import get_db_session
from src.infrastructure.persistence.repositories import (
    PgExecutionRepository,
    PgPipelineRepository,
    PgStepExecutionRepository,
)
from src.infrastructure.security.password_hasher import BcryptPasswordHasher
from src.infrastructure.security.token_service import JwtTokenService
from src.infrastructure.config.settings import get_settings


@dataclass(slots=True, frozen=True)
class CurrentUser:
    sub: str
    role: str


def get_user_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> IUserRepository:
    return PgUserRepository(session)


def get_pipeline_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> IPipelineRepository:
    return PgPipelineRepository(session)


def get_execution_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> IExecutionRepository:
    return PgExecutionRepository(session)


def get_step_execution_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> IStepExecutionRepository:
    return PgStepExecutionRepository(session)


def get_password_hasher() -> IPasswordHasher:
    return BcryptPasswordHasher()


def get_token_service() -> ITokenService:
    settings = get_settings()
    return JwtTokenService(
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_minutes=settings.jwt_access_token_expire_minutes,
    )


def get_login_use_case(
    user_repo: Annotated[IUserRepository, Depends(get_user_repository)],
    password_hasher: Annotated[IPasswordHasher, Depends(get_password_hasher)],
    token_service: Annotated[ITokenService, Depends(get_token_service)],
) -> Login:
    return Login(
        user_repo=user_repo,
        password_hasher=password_hasher,
        token_service=token_service,
    )


def get_start_execution_use_case(
    pipeline_repo: Annotated[IPipelineRepository, Depends(get_pipeline_repository)],
    execution_repo: Annotated[IExecutionRepository, Depends(get_execution_repository)],
    step_execution_repo: Annotated[
        IStepExecutionRepository, Depends(get_step_execution_repository)
    ],
) -> StartExecution:
    return StartExecution(
        pipeline_repo=pipeline_repo,
        execution_repo=execution_repo,
        step_execution_repo=step_execution_repo,
    )


def get_current_user(
    token_service: Annotated[ITokenService, Depends(get_token_service)],
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> CurrentUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
        )

    raw_token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = token_service.decode_access_token(raw_token)
        return CurrentUser(sub=payload.sub, role=payload.role)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from e


def require_admin(
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> CurrentUser:
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )

    return user
