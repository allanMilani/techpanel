from src.application import ConflictAppError
from src.application.dtos import RegisterUserInputDTO, RegisterUserOutputDTO
from src.domain.entities.user import User
from src.domain.ports.repositories import IUserRepository
from src.domain.ports.services import IPasswordHasher
from src.domain.value_objects.user_role import UserRole


class RegisterUser:
    def __init__(
        self,
        user_repo: IUserRepository,
        password_hasher: IPasswordHasher,
    ) -> None:
        self.user_repo = user_repo
        self.password_hasher = password_hasher

    async def execute(self, dto: RegisterUserInputDTO) -> RegisterUserOutputDTO:
        normalized_email = dto.email.strip().lower()
        existing_user = await self.user_repo.get_by_email(normalized_email)
        if existing_user is not None:
            raise ConflictAppError("Email already registered")

        password_hash = self.password_hasher.hash(dto.password)
        created_user = await self.user_repo.create(
            User.create(
                email=normalized_email,
                password_hash=password_hash,
                role=UserRole.VIEWER,
            )
        )

        return RegisterUserOutputDTO(
            user_id=created_user.id,
            email=created_user.email,
            role=created_user.role.value,
        )
