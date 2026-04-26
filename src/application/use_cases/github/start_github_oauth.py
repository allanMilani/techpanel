import secrets

from src.application.dtos.github_dto import GitHubAuthStartOutputDTO
from src.domain.ports.services import IGitHubService


class StartGitHubOAuth:
    def __init__(self, github_service: IGitHubService) -> None:
        self.github_service = github_service

    async def execute(self) -> GitHubAuthStartOutputDTO:
        state = secrets.token_urlsafe(32)
        url = self.github_service.build_authorization_url(state=state)
        return GitHubAuthStartOutputDTO(authorization_url=url, state=state)
