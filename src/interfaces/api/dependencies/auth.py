from dataclasses import dataclass
from typing import Annotated

from fastapi import Cookie, Depends, Header, HTTPException, status

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


def _raw_token_from_request(
    authorization: str | None,
    access_token: str | None,
) -> str | None:
    if authorization and authorization.startswith("Bearer "):
        return authorization.removeprefix("Bearer ").strip()
    if access_token and access_token.strip():
        return access_token.strip()
    return None


def get_optional_current_user(
    token_service: Annotated[ITokenService, Depends(get_token_service)],
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    access_token: Annotated[str | None, Cookie()] = None,
) -> CurrentUser | None:
    raw_token = _raw_token_from_request(authorization, access_token)
    if not raw_token:
        return None
    try:
        payload = token_service.decode_access_token(raw_token)
        return CurrentUser(sub=payload.sub, role=payload.role)
    except Exception:
        return None


def get_current_user(
    token_service: Annotated[ITokenService, Depends(get_token_service)],
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    access_token: Annotated[str | None, Cookie()] = None,
) -> CurrentUser:
    raw_token = _raw_token_from_request(authorization, access_token)

    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization",
        )

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
