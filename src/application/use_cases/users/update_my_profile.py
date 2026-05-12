from dataclasses import replace
from uuid import UUID

from src.application import NotFoundAppError
from src.application.dtos.user_profile_dto import MyProfileOutputDTO, UpdateMyProfileInputDTO
from src.domain.ports.repositories import IUserRepository
from src.domain.ports.services import IKeyCipher


class UpdateMyProfile:
    def __init__(self, user_repo: IUserRepository, key_cipher: IKeyCipher) -> None:
        self.user_repo = user_repo
        self.key_cipher = key_cipher

    async def execute(self, dto: UpdateMyProfileInputDTO) -> MyProfileOutputDTO:
        user = await self.user_repo.get_by_id(dto.user_id)
        if user is None:
            raise NotFoundAppError("User not found")

        if dto.display_name == "keep":
            dn = user.display_name
        else:
            raw = dto.display_name
            if raw is not None and str(raw).strip():
                dn = str(raw).strip()[:255]
            else:
                dn = None

        token_enc: str | None = user.github_token_enc
        if dto.github_token == "clear":
            token_enc = None
        elif dto.github_token != "keep":
            token_enc = self.key_cipher.encrypt(str(dto.github_token).strip())

        updated = replace(user, display_name=dn, github_token_enc=token_enc)
        saved = await self.user_repo.update(updated)
        return MyProfileOutputDTO(
            email=saved.email,
            display_name=saved.display_name,
            has_github_token=bool(saved.github_token_enc),
        )
