from types import SimpleNamespace
from uuid import uuid4

import jwt
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from main import app
from src.application.dtos import ExecutionOutputDTO
from src.infrastructure.config.settings import get_settings
from src.infrastructure.security.password_hasher import BcryptPasswordHasher
from src.infrastructure.security.token_service import JwtTokenService
from src.interfaces.api.dependencies import (
    CurrentUser,
    get_current_user,
    get_start_execution_use_case,
)


def test_bcrypt_password_hasher_hash_and_verify() -> None:
    hasher = BcryptPasswordHasher()
    password_hash = hasher.hash("secret")

    assert password_hash != "secret"
    assert hasher.verify("secret", password_hash) is True
    assert hasher.verify("wrong", password_hash) is False


def test_jwt_token_service_emits_sub_role_and_exp() -> None:
    settings = get_settings()
    service = JwtTokenService(
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_minutes=settings.jwt_access_token_expire_minutes,
    )

    user_id = str(uuid4())
    token = service.create_access_token(sub=user_id, role="admin")
    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )

    assert payload["sub"] == user_id
    assert payload["role"] == "admin"
    assert "exp" in payload


@pytest.mark.asyncio
async def test_get_current_user_rejects_invalid_token() -> None:
    settings = get_settings()
    service = JwtTokenService(
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_minutes=settings.jwt_access_token_expire_minutes,
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(
            token_service=service,
            authorization="Bearer invalid.token.value",
        )
    assert exc_info.value.status_code == 401


def test_viewer_is_blocked_on_execution_start() -> None:
    def stub_start_execution_use_case() -> SimpleNamespace:
        return SimpleNamespace(
            execute=lambda *_args, **_kwargs: ExecutionOutputDTO(
                id=uuid4(),
                pipeline_id=uuid4(),
                status="pending",
                branch_or_tag="main",
            )
        )

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        sub=str(uuid4()), role="viewer"
    )
    app.dependency_overrides[get_start_execution_use_case] = (
        stub_start_execution_use_case
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/executions/start",
            json={"pipeline_id": str(uuid4()), "branch_or_tag": "main"},
            headers={"Authorization": "Bearer any-token"},
        )

    app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin role required"


def test_admin_can_start_execution() -> None:
    class StartExecutionStub:
        async def execute(self, *_args, **_kwargs) -> ExecutionOutputDTO:
            return ExecutionOutputDTO(
                id=uuid4(),
                pipeline_id=uuid4(),
                status="pending",
                branch_or_tag="main",
            )

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        sub=str(uuid4()), role="admin"
    )
    app.dependency_overrides[get_start_execution_use_case] = lambda: (
        StartExecutionStub()
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/executions/start",
            json={"pipeline_id": str(uuid4()), "branch_or_tag": "main"},
            headers={"Authorization": "Bearer any-token"},
        )

    app.dependency_overrides.clear()

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending"
    assert body["branch_or_tag"] == "main"
