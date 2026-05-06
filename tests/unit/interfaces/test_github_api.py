from fastapi.testclient import TestClient

from main import app
from src.interfaces.api.dependencies import CurrentUser
from src.interfaces.api.dependencies import get_current_user
from src.interfaces.api.dependencies.github import (
    get_handle_github_oauth_callback_use_case,
    get_list_github_refs_use_case,
    get_list_github_repositories_use_case,
    get_start_github_oauth_use_case,
)


class StartOAuthStub:
    async def execute(self):
        class Out:
            authorization_url = "https://github.com/login/oauth/authorize?state=abc"
            state = "abc"

        return Out()


class CallbackStub:
    async def execute(self, _dto, expected_state):
        class Out:
            access_token = "gho_xxx"
            token_type = "bearer"

        _ = expected_state
        return Out()


class ReposStub:
    async def execute(self, access_token: str):
        _ = access_token

        class Repo:
            def __init__(self, full_name: str) -> None:
                self.full_name = full_name

        return [Repo("org/repo-a")]


class RefsStub:
    async def execute(self, access_token: str, repository: str):
        _ = access_token
        _ = repository

        class Out:
            branches = ["main"]
            tags = ["v1.0.0"]

        return Out()


def test_github_api_routes_happy_path() -> None:
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        sub="00000000-0000-0000-0000-000000000001", role="admin"
    )
    app.dependency_overrides[get_start_github_oauth_use_case] = lambda: StartOAuthStub()
    app.dependency_overrides[get_handle_github_oauth_callback_use_case] = lambda: (
        CallbackStub()
    )
    app.dependency_overrides[get_list_github_repositories_use_case] = lambda: (
        ReposStub()
    )
    app.dependency_overrides[get_list_github_refs_use_case] = lambda: RefsStub()

    with TestClient(app) as client:
        client.cookies.set("github_oauth_state", "ok")

        r1 = client.get("/api/auth/github", headers={"Authorization": "Bearer any"})
        assert r1.status_code == 200
        assert "authorization_url" in r1.json()

        r2 = client.get(
            "/api/auth/github/callback?code=abc&state=ok",
            headers={"Authorization": "Bearer any"},
        )
        assert r2.status_code == 200
        assert r2.json()["token_type"] == "bearer"

        r3 = client.get(
            "/api/github/repos",
            headers={"Authorization": "Bearer any", "X-GitHub-Token": "gho_xxx"},
        )
        assert r3.status_code == 200
        body = r3.json()
        assert body["items"][0]["full_name"] == "org/repo-a"

        r4 = client.get(
            "/api/github/repos/org%2Frepo-a/refs",
            headers={"Authorization": "Bearer any", "X-GitHub-Token": "gho_xxx"},
        )
        assert r4.status_code == 200
        assert r4.json()["branches"] == ["main"]
        assert r4.json()["tags"] == ["v1.0.0"]

    app.dependency_overrides.clear()
