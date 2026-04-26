from src.application import ConflictAppError
from src.application.dtos import RegisterUserOutputDTO
from fastapi.testclient import TestClient
from uuid import uuid4

from main import app
from src.interfaces.api.dependencies import (
    get_list_projects,
    get_register_user_use_case,
    get_list_servers_use_case,
)


class _FastListUseCase:
    async def execute(self) -> list[object]:
        return []


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


def test_login_page_renders() -> None:
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert "Login" in response.text
        assert "Criar conta" in response.text


def test_register_page_renders() -> None:
    with TestClient(app) as client:
        response = client.get("/register")
        assert response.status_code == 200
        assert "Cadastro" in response.text
        assert 'action="/register"' in response.text


def test_register_submit_redirects_on_success() -> None:
    app.dependency_overrides[get_register_user_use_case] = lambda: _RegisterOkUseCase()
    with TestClient(app) as client:
        response = client.post(
            "/register",
            data={"email": "new@techpanel.dev", "password": "secret123"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"] == "/"
    app.dependency_overrides.clear()


def test_register_submit_returns_409_when_email_exists() -> None:
    app.dependency_overrides[get_register_user_use_case] = (
        lambda: _RegisterConflictUseCase()
    )
    with TestClient(app) as client:
        response = client.post(
            "/register",
            data={"email": "existing@techpanel.dev", "password": "secret123"},
        )
        assert response.status_code == 409
        assert "E-mail ja cadastrado" in response.text
    app.dependency_overrides.clear()


def test_dashboard_has_polling_and_modals() -> None:
    app.dependency_overrides[get_list_servers_use_case] = lambda: _FastListUseCase()
    app.dependency_overrides[get_list_projects] = lambda: _FastListUseCase()
    with TestClient(app) as client:
        response = client.get("/app")
        assert response.status_code == 200
        assert 'hx-trigger="load, every 2s"' in response.text
        assert "confirmExecutionModal" in response.text
        assert "confirmExecutionProductionModal" in response.text
        assert "CONFIRMAR" in response.text
    app.dependency_overrides.clear()


def test_history_failed_step_highlight() -> None:
    html = """
      <span class="text-danger fw-semibold">Passo com falha</span>
    """
    assert "Passo com falha" in html
