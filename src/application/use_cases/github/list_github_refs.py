from src.application.dtos.github_dto import GitHubRefsDTO
from src.domain.ports.services import IGitHubService


class ListGitHubRefs:
    def __init__(self, github_service: IGitHubService) -> None:
        self.github_service = github_service

    async def execute(self, access_token: str, repository: str) -> GitHubRefsDTO:
        branches = await self.github_service.list_branches(
            repository=repository,
            access_token=access_token,
        )
        tags = await self.github_service.list_tags(
            repository=repository,
            access_token=access_token,
        )
        return GitHubRefsDTO(branches=branches, tags=tags)
