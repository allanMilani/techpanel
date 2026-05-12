from types import SimpleNamespace
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from main import app
from src.interfaces.api.dependencies import (
    CurrentUser,
    get_check_ssh_connection_use_case,
    get_create_server_use_case,
    get_delete_server_use_case,
    get_list_servers_use_case,
    get_update_server_use_case,
    get_current_user,
)
from src.interfaces.api.dependencies.core import get_user_repository

_ADMIN_ID = uuid4()


def _admin_user() -> CurrentUser:
    return CurrentUser(sub=str(_ADMIN_ID), role="admin")


class _StubUserRepo:
    """Utilizador da sessão existe (evita depender da BD nos testes de router)."""

    async def get_by_id(self, uid: UUID) -> object | None:
        if uid == _ADMIN_ID:
            return object()
        return None


def test_list_servers_router() -> None:
    sid = uuid4()
    cid = uuid4()

    async def execute(_page: int, _per_page: int):
        return SimpleNamespace(
            items=[
                SimpleNamespace(
                    id=sid,
                    name="srv-1",
                    host="10.0.0.1",
                    port=22,
                    ssh_user="ubuntu",
                    created_by=cid,
                    connection_kind="ssh",
                    docker_container_name=None,
                    ssh_strict_host_key_checking=False,
                    project_directory=None,
                )
            ],
            total=1,
            page=1,
            per_page=20,
            total_pages=1,
        )

    app.dependency_overrides[get_current_user] = _admin_user
    app.dependency_overrides[get_list_servers_use_case] = lambda: SimpleNamespace(
        execute=execute
    )

    with TestClient(app) as client:
        response = client.get("/api/servers/", headers={"Authorization": "Bearer x"})

    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["name"] == "srv-1"
    assert body["items"][0]["ssh_strict_host_key_checking"] is False
    assert "private_key_plain" not in body["items"][0]


def test_create_server_router() -> None:
    server_id = uuid4()
    created_by = uuid4()

    async def execute(_dto):
        return SimpleNamespace(
            id=server_id,
            name="srv-new",
            host="10.0.0.2",
            port=22,
            ssh_user="deploy",
            created_by=created_by,
            connection_kind="ssh",
            docker_container_name=None,
            ssh_strict_host_key_checking=False,
            project_directory=None,
        )

    app.dependency_overrides[get_current_user] = _admin_user
    app.dependency_overrides[get_user_repository] = lambda: _StubUserRepo()
    app.dependency_overrides[get_create_server_use_case] = lambda: SimpleNamespace(
        execute=execute
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/servers/",
            headers={"Authorization": "Bearer x"},
            json={
                "name": "srv-new",
                "host": "10.0.0.2",
                "port": 22,
                "ssh_user": "deploy",
                "private_key_plain": "PRIVATE_KEY",
            },
        )

    app.dependency_overrides.clear()

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == str(server_id)
    assert body["created_by"] == str(created_by)
    assert body["ssh_strict_host_key_checking"] is False
    assert "private_key_plain" not in body


def test_update_server_router() -> None:
    target_id = uuid4()
    created_by = uuid4()

    async def execute(_server_id, _dto):
        return SimpleNamespace(
            id=target_id,
            name="srv-updated",
            host="10.0.0.3",
            port=2222,
            ssh_user="root",
            created_by=created_by,
            connection_kind="ssh",
            docker_container_name=None,
            ssh_strict_host_key_checking=True,
            project_directory=None,
        )

    app.dependency_overrides[get_current_user] = _admin_user
    app.dependency_overrides[get_update_server_use_case] = lambda: SimpleNamespace(
        execute=execute
    )

    with TestClient(app) as client:
        response = client.put(
            f"/api/servers/{target_id}",
            headers={"Authorization": "Bearer x"},
            json={
                "name": "srv-updated",
                "host": "10.0.0.3",
                "port": 2222,
                "ssh_user": "root",
                "private_key_plain": None,
                "ssh_strict_host_key_checking": True,
            },
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["name"] == "srv-updated"
    assert response.json()["ssh_strict_host_key_checking"] is True


def test_delete_server_router() -> None:
    target_id = uuid4()

    async def execute(_server_id):
        return None

    app.dependency_overrides[get_current_user] = _admin_user
    app.dependency_overrides[get_delete_server_use_case] = lambda: SimpleNamespace(
        execute=execute
    )

    with TestClient(app) as client:
        response = client.delete(
            f"/api/servers/{target_id}",
            headers={"Authorization": "Bearer x"},
        )

    app.dependency_overrides.clear()

    assert response.status_code == 204


def test_test_connection_router() -> None:
    target_id = uuid4()

    async def execute(_server_id):
        return True, None, None

    app.dependency_overrides[get_current_user] = _admin_user
    app.dependency_overrides[get_check_ssh_connection_use_case] = lambda: (
        SimpleNamespace(execute=execute)
    )

    with TestClient(app) as client:
        response = client.post(
            f"/api/servers/{target_id}/test",
            headers={"Authorization": "Bearer x"},
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "ok": True,
        "error_code": None,
        "error_detail": None,
    }
