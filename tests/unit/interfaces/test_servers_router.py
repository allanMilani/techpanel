from types import SimpleNamespace
from uuid import uuid4

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


def _admin_user() -> CurrentUser:
    return CurrentUser(sub=str(uuid4()), role="admin")


def test_list_servers_router() -> None:
    async def execute():
        return [
            SimpleNamespace(
                id=uuid4(),
                name="srv-1",
                host="10.0.0.1",
                port=22,
                ssh_user="ubuntu",
                created_by=uuid4(),
                connection_kind="ssh",
                docker_container_name=None,
            )
        ]

    app.dependency_overrides[get_current_user] = _admin_user
    app.dependency_overrides[get_list_servers_use_case] = lambda: SimpleNamespace(
        execute=execute
    )

    with TestClient(app) as client:
        response = client.get("/api/servers", headers={"Authorization": "Bearer x"})

    app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["name"] == "srv-1"
    assert "private_key_plain" not in body[0]


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
        )

    app.dependency_overrides[get_current_user] = _admin_user
    app.dependency_overrides[get_create_server_use_case] = lambda: SimpleNamespace(
        execute=execute
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/servers",
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
            },
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["name"] == "srv-updated"


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
        return True

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
    assert response.json() == {"ok": True}
