from dataclasses import replace
from uuid import uuid4

import pytest

from src.application import UnauthorizedAppError, ValidationAppError
from src.application.dtos.github_dto import GitHubAuthCallbackInputDTO
from src.application.use_cases.github.handle_github_oauth_callback import (
    HandleGitHubOAuthCallback,
)
from src.application.use_cases.github.list_github_refs import ListGitHubRefs
from src.application.use_cases.github.list_github_repositories import (
    ListGitHubRepositories,
)
from src.application.use_cases.github.list_my_github_repositories import (
    ListMyGitHubRepositories,
)
from src.application.use_cases.github.search_my_github_refs import SearchMyGitHubRefs
from src.application.use_cases.github.start_github_oauth import StartGitHubOAuth
from src.domain.entities.user import User
from src.domain.value_objects.user_role import UserRole


class FakeGitHubService:
    def build_authorization_url(self, state: str) -> str:
        return f"https://github.com/login/oauth/authorize?state={state}"

    async def exchange_code_for_token(self, code: str) -> tuple[str, str]:
        return (f"token-{code}", "bearer")

    async def list_repositories(self, access_token: str) -> list[str]:
        _ = access_token
        return ["org/repo-a", "org/repo-b"]

    async def list_branches(self, repository: str, access_token: str) -> list[str]:
        _ = repository
        _ = access_token
        return ["main", "develop"]

    async def list_tags(self, repository: str, access_token: str) -> list[str]:
        _ = repository
        _ = access_token
        return ["v1.0.0"]

    async def ref_exists(
        self, repository: str, ref_name: str, access_token: str
    ) -> bool:
        _ = repository
        _ = access_token
        return ref_name in {"main", "develop", "v1.0.0"}

    async def search_repositories(
        self, access_token: str, query: str, page: int, per_page: int
    ) -> tuple[list[str], int]:
        _ = access_token
        _ = query
        _ = page
        _ = per_page
        return (["org/repo-a", "org/repo-b"], 2)

    async def search_refs(
        self, access_token: str, repository: str, query: str, limit: int
    ) -> tuple[list[str], list[str]]:
        _ = access_token
        _ = repository
        _ = query
        _ = limit
        return (["main", "develop"], ["v1.0.0"])


class _CipherStub:
    def encrypt(self, plain_text: str) -> str:
        return f"e:{plain_text}"

    def decrypt(self, cipher_text: str) -> str:
        return cipher_text.split(":", 1)[1]


class _UserRepoWithToken:
    def __init__(self, user: User) -> None:
        self.user = user

    async def get_by_id(self, user_id):
        return self.user if self.user.id == user_id else None


@pytest.mark.asyncio
async def test_start_oauth_generates_url_and_state() -> None:
    uc = StartGitHubOAuth(FakeGitHubService())
    out = await uc.execute()
    assert "github.com/login/oauth/authorize" in out.authorization_url
    assert out.state


@pytest.mark.asyncio
async def test_callback_exchanges_code_when_state_matches() -> None:
    uc = HandleGitHubOAuthCallback(FakeGitHubService())
    out = await uc.execute(
        GitHubAuthCallbackInputDTO(code="abc", state="state-ok"),
        expected_state="state-ok",
    )
    assert out.access_token == "token-abc"


@pytest.mark.asyncio
async def test_callback_rejects_invalid_state() -> None:
    uc = HandleGitHubOAuthCallback(FakeGitHubService())
    with pytest.raises(UnauthorizedAppError):
        await uc.execute(
            GitHubAuthCallbackInputDTO(code="abc", state="wrong"),
            expected_state="right",
        )


@pytest.mark.asyncio
async def test_list_repositories() -> None:
    uc = ListGitHubRepositories(FakeGitHubService())
    out = await uc.execute("token")
    assert [x.full_name for x in out] == ["org/repo-a", "org/repo-b"]


@pytest.mark.asyncio
async def test_list_refs() -> None:
    uc = ListGitHubRefs(FakeGitHubService())
    out = await uc.execute(access_token="token", repository="org/repo-a")
    assert out.branches == ["main", "develop"]
    assert out.tags == ["v1.0.0"]


@pytest.mark.asyncio
async def test_list_my_github_repositories_requires_token() -> None:
    uid = uuid4()
    u = replace(User.create("a@b.dev", "h", UserRole.VIEWER), id=uid)
    uc = ListMyGitHubRepositories(_UserRepoWithToken(u), _CipherStub(), FakeGitHubService())
    with pytest.raises(ValidationAppError):
        await uc.execute(uid, "", 1, 20)


@pytest.mark.asyncio
async def test_list_my_github_repositories_with_token() -> None:
    uid = uuid4()
    cipher = _CipherStub()
    u = replace(
        User.create("a@b.dev", "h", UserRole.VIEWER),
        id=uid,
        github_token_enc=cipher.encrypt("tok"),
    )
    uc = ListMyGitHubRepositories(_UserRepoWithToken(u), cipher, FakeGitHubService())
    items, total = await uc.execute(uid, "app", 1, 20)
    assert total == 2
    assert [x.full_name for x in items] == ["org/repo-a", "org/repo-b"]


@pytest.mark.asyncio
async def test_search_my_github_refs_with_token() -> None:
    uid = uuid4()
    cipher = _CipherStub()
    u = replace(
        User.create("a@b.dev", "h", UserRole.VIEWER),
        id=uid,
        github_token_enc=cipher.encrypt("tok"),
    )
    uc = SearchMyGitHubRefs(_UserRepoWithToken(u), cipher, FakeGitHubService())
    out = await uc.execute(uid, "org/app", "ma", 50)
    assert out.branches == ["main", "develop"]
    assert out.tags == ["v1.0.0"]
