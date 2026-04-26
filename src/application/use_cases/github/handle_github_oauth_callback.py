from src.application import UnauthorizedAppError
from src.application.dtos.github_dto import (
    GitHubAuthCallbackInputDTO,
    GitHubAuthCallbackOutputDTO,
)
from src.domain.ports.services import IGitHubService


class HandleGitHubOAuthCallback:
    def __init__(self, github_service: IGitHubService) -> None:
        self.github_service = github_service

    async def execute(
        self,
        dto: GitHubAuthCallbackInputDTO,
        expected_state: str,
    ) -> GitHubAuthCallbackOutputDTO:
        if dto.state != expected_state:
            raise UnauthorizedAppError("Invalid OAuth state")

        token, token_type = await self.github_service.exchange_code_for_token(dto.code)
        return GitHubAuthCallbackOutputDTO(
            access_token=token,
            token_type=token_type,
        )
