from uuid import uuid4

from fastapi.testclient import TestClient

from main import app
from src.application import ConflictAppError
from src.application.dtos import RegisterUserOutputDTO
from src.interfaces.api.dependencies import get_register_user_use_case


class _RegisterOkUseCase:
    async def execute(self, dto) -> RegisterUserOutputDTO:
        return RegisterUserOutputDTO(
            user_id=uuid4(),
            email=dto.email.strip().lower(),
            role="viewer",
        )


class _RegisterConflictUseCase:
    async def execute(self, dto) -> RegisterUserOutputDTO:
        _ = dto
        raise ConflictAppError("Email already registered")


def test_spa_shell_served_at_root_when_built(monkeypatch) -> None:
    monkeypatch.setenv("FRONTEND_DEV_SERVER_URL", "")
    from src.infrastructure.config.settings import get_settings

    get_settings.cache_clear()
    with TestClient(app) as client:
        response = client.get("/")
    get_settings.cache_clear()
    assert response.status_code == 200
    assert 'id="app"' in response.text


def test_spa_shell_at_app_path(monkeypatch) -> None:
    monkeypatch.setenv("FRONTEND_DEV_SERVER_URL", "")
    from src.infrastructure.config.settings import get_settings

    get_settings.cache_clear()
    with TestClient(app) as client:
        response = client.get("/app/pipelines")
    get_settings.cache_clear()
    assert response.status_code == 200
    assert 'id="app"' in response.text


def test_register_json_returns_201() -> None:
    app.dependency_overrides[get_register_user_use_case] = lambda: _RegisterOkUseCase()
    with TestClient(app) as client:
        response = client.post(
            "/api/auth/register",
            json={"email": "new@techpanel.dev", "password": "secret123"},
        )
    app.dependency_overrides.clear()
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "new@techpanel.dev"
    assert data["role"] == "viewer"
    assert "user_id" in data


def test_register_json_returns_409_when_email_exists() -> None:
    app.dependency_overrides[get_register_user_use_case] = lambda: (
        _RegisterConflictUseCase()
    )
    with TestClient(app) as client:
        response = client.post(
            "/api/auth/register",
            json={"email": "existing@techpanel.dev", "password": "secret123"},
        )
    app.dependency_overrides.clear()
    assert response.status_code == 409
    assert "detail" in response.json()


def test_auth_me_without_cookie_returns_401() -> None:
    with TestClient(app) as client:
        response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_logout_api_returns_204() -> None:
    with TestClient(app) as client:
        response = client.post("/api/auth/logout")
    assert response.status_code == 204
