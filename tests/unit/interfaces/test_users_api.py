from uuid import uuid4

from fastapi.testclient import TestClient

from main import app
from src.application.dtos.github_dto import GitHubRefsDTO, GitHubRepositoryDTO
from src.application.dtos.user_profile_dto import MyProfileOutputDTO
from src.interfaces.api.dependencies import (
    CurrentUser,
    get_current_user,
    get_get_my_profile_use_case,
    get_list_my_github_repositories_use_case,
    get_search_my_github_refs_use_case,
    get_update_my_profile_use_case,
)


def test_profile_get_and_patch() -> None:
    uid = str(uuid4())

    class GetProfileStub:
        async def execute(self, _user_id):
            return MyProfileOutputDTO(
                email="a@b.com",
                display_name="Alice",
                has_github_token=True,
            )

    class UpdateProfileStub:
        async def execute(self, _dto):
            return MyProfileOutputDTO(
                email="a@b.com",
                display_name="Bob",
                has_github_token=False,
            )

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(sub=uid, role="viewer")
    app.dependency_overrides[get_get_my_profile_use_case] = lambda: GetProfileStub()
    app.dependency_overrides[get_update_my_profile_use_case] = lambda: UpdateProfileStub()

    with TestClient(app) as client:
        r = client.get("/api/users/me/profile", headers={"Authorization": "Bearer t"})
        assert r.status_code == 200
        j = r.json()
        assert j["email"] == "a@b.com"
        assert j["display_name"] == "Alice"
        assert j["has_github_token"] is True

        r2 = client.patch(
            "/api/users/me/profile",
            headers={"Authorization": "Bearer t"},
            json={"display_name": "Bob", "github_token": ""},
        )
        assert r2.status_code == 200
        assert r2.json()["display_name"] == "Bob"
        assert r2.json()["has_github_token"] is False

    app.dependency_overrides.clear()


def test_my_github_repos_and_refs() -> None:
    uid = str(uuid4())

    class ListMyStub:
        async def execute(self, _user_id, _q, _page, _per_page):
            return ([GitHubRepositoryDTO(full_name="org/app")], 1)

    class SearchMyStub:
        async def execute(self, _user_id, _repository, _q, _limit):
            return GitHubRefsDTO(branches=["main"], tags=["v1"])

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(sub=uid, role="admin")
    app.dependency_overrides[get_list_my_github_repositories_use_case] = lambda: ListMyStub()
    app.dependency_overrides[get_search_my_github_refs_use_case] = lambda: SearchMyStub()

    with TestClient(app) as client:
        r = client.get(
            "/api/users/me/github/repos?q=app",
            headers={"Authorization": "Bearer t"},
        )
        assert r.status_code == 200
        assert r.json()["items"][0]["full_name"] == "org/app"

        r2 = client.get(
            "/api/users/me/github/repos/org%2Fapp/refs?q=ma",
            headers={"Authorization": "Bearer t"},
        )
        assert r2.status_code == 200
        body = r2.json()
        assert body["branches"] == ["main"]
        assert body["tags"] == ["v1"]

    app.dependency_overrides.clear()
