import pytest

from src.application import UnauthorizedAppError
from src.application.dtos.github_dto import GitHubAuthCallbackInputDTO
from src.application.use_cases.github.handle_github_oauth_callback import (
    HandleGitHubOAuthCallback,
)
from src.application.use_cases.github.list_github_refs import ListGitHubRefs
from src.application.use_cases.github.list_github_repositories import (
    ListGitHubRepositories,
)
from src.application.use_cases.github.start_github_oauth import StartGitHubOAuth


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
