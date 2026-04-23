from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.ports.repositories import (
    IExecutionRepository,
    IPipelineRepository,
    IStepExecutionRepository,
    IServerRepository,
    IUserRepository,
)
from src.infrastructure.persistence.database import get_db_session
from src.infrastructure.persistence.repositories import (
    PgExecutionRepository,
    PgPipelineRepository,
    PgStepExecutionRepository,
)
from src.infrastructure.persistence.repositories.pg_server_repository import (
    PgServerRepository,
)
from src.infrastructure.persistence.repositories.pg_user_repository import (
    PgUserRepository,
)


def get_user_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> IUserRepository:
    return PgUserRepository(session)


def get_server_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> IServerRepository:
    return PgServerRepository(session)


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
