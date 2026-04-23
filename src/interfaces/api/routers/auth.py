from typing import Annotated
from fastapi import APIRouter, Depends, status
from src.application.dtos import LoginInputDTO
from src.application.use_cases.auth.login import Login
from src.interfaces.api.dependencies import get_login_use_case
from src.interfaces.api.schemas import LoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(
    payload: LoginRequest, use_case: Annotated[Login, Depends(get_login_use_case)]
) -> LoginResponse:
    out = await use_case.execute(
        LoginInputDTO(
            email=payload.email,
            password=payload.password,
        )
    )

    return LoginResponse(
        access_token=out.access_token,
        token_type=out.token_type,
        user_id=str(out.user_id),
        role=out.role,
    )
