from src.application.dtos.github_dto import GitHubRepositoryDTO
from src.domain.ports.services import IGitHubService


class ListGitHubRepositories:
    def __init__(self, github_service: IGitHubService) -> None:
        self.github_service = github_service

    async def execute(self, access_token: str) -> list[GitHubRepositoryDTO]:
        repos = await self.github_service.list_repositories(access_token=access_token)
        return [GitHubRepositoryDTO(full_name=repo) for repo in repos]
