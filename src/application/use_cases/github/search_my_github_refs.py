from uuid import UUID

from src.application import ValidationAppError
from src.application.dtos.github_dto import GitHubRefsDTO
from src.domain.ports.repositories import IUserRepository
from src.domain.ports.services import IGitHubService, IKeyCipher


class SearchMyGitHubRefs:
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
        self, user_id: UUID, repository: str, q: str, limit: int
    ) -> GitHubRefsDTO:
        user = await self.user_repo.get_by_id(user_id)
        if user is None or not user.github_token_enc:
            raise ValidationAppError(
                "Configure um token GitHub em Perfil para listar branches e tags."
            )
        token = self.key_cipher.decrypt(user.github_token_enc)
        branches, tags = await self.github_service.search_refs(
            token, repository, q, limit
        )
        return GitHubRefsDTO(branches=branches, tags=tags)
