from __future__ import annotations

import httpx
from github import Github

from src.application import ValidationAppError
from src.domain.ports.services import IGitHubService


class PyGitHubService(IGitHubService):
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        callback_url: str,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.callback_url = callback_url

    def build_authorization_url(self, state: str) -> str:
        return (
            "https://github.com/login/oauth/authorize"
            f"?client_id={self.client_id}"
            f"&redirect_uri={self.callback_url}"
            "&scope=repo,read:org"
            f"&state={state}"
        )

    async def exchange_code_for_token(self, code: str) -> tuple[str, str]:
        url = "https://github.com/login/oauth/access_token"
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
        }
        headers = {"Accept": "application/json"}

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(url, json=payload, headers=headers)

        data = response.json()
        token = data.get("access_token")
        token_type = data.get("token_type", "bearer")

        if not token:
            raise ValidationAppError("Could not retrieve GitHub access token")

        return token, token_type

    async def list_repositories(self, access_token: str) -> list[str]:
        gh = Github(access_token)
        user = gh.get_user()
        return [repo.full_name for repo in user.get_repos()]

    async def list_branches(self, repository: str, access_token: str) -> list[str]:
        gh = Github(access_token)
        repo = gh.get_repo(repository)
        return [branch.name for branch in repo.get_branches()]

    async def list_tags(self, repository: str, access_token: str) -> list[str]:
        gh = Github(access_token)
        repo = gh.get_repo(repository)
        return [tag.name for tag in repo.get_tags()]

    async def ref_exists(
        self, repository: str, ref_name: str, access_token: str
    ) -> bool:
        branches = await self.list_branches(repository, access_token)
        tags = await self.list_tags(repository, access_token)
        return ref_name in branches or ref_name in tags
