from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from starlette.responses import Response

from src.application import ConflictAppError
from src.application.dtos import LoginInputDTO
from src.application.dtos.auth_dto import RegisterUserInputDTO
from src.application.use_cases.auth.login import Login
from src.application.use_cases.auth.register_user import RegisterUser
from src.domain.ports.repositories import IUserRepository
from src.interfaces.api.dependencies import (
    get_login_use_case,
    get_optional_current_user,
    get_register_user_use_case,
    get_user_repository,
)
from src.interfaces.api.dependencies.auth import CurrentUser
from src.interfaces.api.schemas import (
    LoginRequest,
    LoginResponse,
    MeResponse,
    RegisterRequest,
    RegisterResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=MeResponse, status_code=status.HTTP_200_OK)
async def auth_me(
    user: Annotated[CurrentUser | None, Depends(get_optional_current_user)],
    user_repo: Annotated[IUserRepository, Depends(get_user_repository)],
) -> MeResponse:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    row = await user_repo.get_by_id(UUID(user.sub))
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return MeResponse(
        user_id=user.sub,
        role=user.role,
        display_name=row.display_name,
        has_github_token=bool(row.github_token_enc),
    )


@router.post(
    "/session",
    response_model=MeResponse,
    status_code=status.HTTP_200_OK,
)
async def login_session(
    payload: LoginRequest,
    response: Response,
    use_case: Annotated[Login, Depends(get_login_use_case)],
) -> MeResponse:
    try:
        out = await use_case.execute(
            LoginInputDTO(
                email=str(payload.email),
                password=payload.password,
            )
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
        ) from e

    response.set_cookie(
        "access_token",
        out.access_token,
        httponly=True,
        samesite="lax",
    )
    return MeResponse(
        user_id=str(out.user_id),
        role=out.role,
        display_name=out.display_name,
        has_github_token=out.has_github_token,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout_session() -> Response:
    r = Response(status_code=status.HTTP_204_NO_CONTENT)
    r.delete_cookie("access_token")
    return r


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_json(
    payload: RegisterRequest,
    use_case: Annotated[RegisterUser, Depends(get_register_user_use_case)],
) -> RegisterResponse:
    try:
        out = await use_case.execute(
            RegisterUserInputDTO(
                email=str(payload.email),
                password=payload.password,
                display_name=(payload.name.strip() if payload.name else None),
            )
        )
    except ConflictAppError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nao foi possivel concluir o cadastro",
        ) from e

    return RegisterResponse(
        user_id=str(out.user_id),
        email=out.email,
        role=out.role,
    )


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(
    payload: LoginRequest, use_case: Annotated[Login, Depends(get_login_use_case)]
) -> LoginResponse:
    out = await use_case.execute(
        LoginInputDTO(
            email=str(payload.email),
            password=payload.password,
        )
    )

    return LoginResponse(
        access_token=out.access_token,
        token_type=out.token_type,
        user_id=str(out.user_id),
        role=out.role,
    )
