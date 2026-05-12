from src.application import UnauthorizedAppError
from src.application.dtos import LoginInputDTO, LoginOutputDTO
from src.domain.ports.repositories import IUserRepository


class Login:
    def __init__(
        self, user_repo: IUserRepository, password_hasher, token_service
    ) -> None:
        self.user_repo = user_repo
        self.password_hasher = password_hasher
        self.token_service = token_service

    async def execute(self, dto: LoginInputDTO) -> LoginOutputDTO:
        user = await self.user_repo.get_by_email(dto.email.strip().lower())

        if user is None:
            raise UnauthorizedAppError("Invalid email or password")

        if not self.password_hasher.verify(dto.password, user.password_hash):
            raise UnauthorizedAppError("Invalid email or password")

        token = self.token_service.create_access_token(
            sub=str(user.id), role=user.role.value
        )

        return LoginOutputDTO(
            access_token=token,
            token_type="Bearer",
            user_id=user.id,
            role=user.role.value,
            display_name=user.display_name,
            has_github_token=bool(user.github_token_enc),
        )
