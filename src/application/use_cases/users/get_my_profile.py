from uuid import UUID

from src.application import NotFoundAppError
from src.application.dtos.user_profile_dto import MyProfileOutputDTO
from src.domain.ports.repositories import IUserRepository


class GetMyProfile:
    def __init__(self, user_repo: IUserRepository) -> None:
        self.user_repo = user_repo

    async def execute(self, user_id: UUID) -> MyProfileOutputDTO:
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundAppError("User not found")
        return MyProfileOutputDTO(
            email=user.email,
            display_name=user.display_name,
            has_github_token=bool(user.github_token_enc),
        )
