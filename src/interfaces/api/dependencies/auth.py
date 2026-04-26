from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from src.application.use_cases.auth.login import Login
from src.application.use_cases.auth.register_user import RegisterUser
from src.domain.ports.repositories import IUserRepository
from src.domain.ports.services import IPasswordHasher, ITokenService
from src.infrastructure.config.settings import get_settings
from src.infrastructure.security.password_hasher import BcryptPasswordHasher
from src.infrastructure.security.token_service import JwtTokenService
from src.interfaces.api.dependencies.core import get_user_repository


@dataclass(slots=True, frozen=True)
class CurrentUser:
    sub: str
    role: str


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


def get_register_user_use_case(
    user_repo: Annotated[IUserRepository, Depends(get_user_repository)],
    password_hasher: Annotated[IPasswordHasher, Depends(get_password_hasher)],
) -> RegisterUser:
    return RegisterUser(
        user_repo=user_repo,
        password_hasher=password_hasher,
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
