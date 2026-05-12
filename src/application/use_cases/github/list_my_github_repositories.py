from uuid import UUID

from src.application import ValidationAppError
from src.application.dtos.github_dto import GitHubRepositoryDTO
from src.domain.ports.repositories import IUserRepository
from src.domain.ports.services import IGitHubService, IKeyCipher


class ListMyGitHubRepositories:
    def __init__(
        self,
        user_repo: IUserRepository,
        key_cipher: IKeyCipher,
        github_service: IGitHubService,
    ) -> None:
        self.user_repo = user_repo
        self.key_cipher = key_cipher
        self.github_service = github_service

    async def execute(
        self, user_id: UUID, q: str, page: int, per_page: int
    ) -> tuple[list[GitHubRepositoryDTO], int]:
        user = await self.user_repo.get_by_id(user_id)
        if user is None or not user.github_token_enc:
            raise ValidationAppError(
                "Configure um token GitHub em Perfil para listar repositórios."
            )
        token = self.key_cipher.decrypt(user.github_token_enc)
        names, total = await self.github_service.search_repositories(
            token, q, page, per_page
        )
        return [GitHubRepositoryDTO(full_name=n) for n in names], total
