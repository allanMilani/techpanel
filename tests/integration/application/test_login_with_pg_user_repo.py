import pytest

from src.application import UnauthorizedAppError
from src.application.dtos import LoginInputDTO
from src.application.use_cases.auth.login import Login
from src.domain.entities.user import User
from src.domain.value_objects.user_role import UserRole
from tests.unit.application.fakes import FakePasswordHasher, FakeTokenService


class MemoryUserRepo:
    def __init__(self) -> None:
        self.items: dict[str, User] = {}

    async def create(self, user: User) -> User:
        self.items[user.email] = user
        return user

    async def get_by_id(self, user_id):
        return next((u for u in self.items.values() if u.id == user_id), None)

    async def get_by_email(self, email: str) -> User | None:
        return self.items.get(email)


@pytest.mark.asyncio
async def test_login_with_mocked_user_repo_success() -> None:
    user_repo = MemoryUserRepo()
    use_case = Login(
        user_repo=user_repo,
        password_hasher=FakePasswordHasher("secret"),
        token_service=FakeTokenService(),
    )

    created_user = await user_repo.create(
        User.create(
            email="admin.integration@techpanel.dev",
            password_hash="stored-hash",
            role=UserRole.ADMIN,
        )
    )

    output = await use_case.execute(
        LoginInputDTO(
            email="  ADMIN.INTEGRATION@techpanel.dev  ",  # valida normalize strip/lower
            password="secret",
        )
    )

    assert output.user_id == created_user.id
    assert output.role == UserRole.ADMIN.value
    assert output.token_type == "Bearer"
    assert output.access_token.startswith("token.")


@pytest.mark.asyncio
async def test_login_with_mocked_user_repo_fails_when_email_not_found() -> None:
    user_repo = MemoryUserRepo()
    use_case = Login(
        user_repo=user_repo,
        password_hasher=FakePasswordHasher("secret"),
        token_service=FakeTokenService(),
    )

    with pytest.raises(UnauthorizedAppError, match="Invalid email or password"):
        await use_case.execute(
            LoginInputDTO(email="missing@techpanel.dev", password="secret")
        )


@pytest.mark.asyncio
async def test_login_with_mocked_user_repo_fails_when_password_is_invalid() -> None:
    user_repo = MemoryUserRepo()
    use_case = Login(
        user_repo=user_repo,
        password_hasher=FakePasswordHasher("right-password"),
        token_service=FakeTokenService(),
    )

    await user_repo.create(
        User.create(
            email="viewer.integration@techpanel.dev",
            password_hash="stored-hash",
            role=UserRole.VIEWER,
        )
    )

    with pytest.raises(UnauthorizedAppError, match="Invalid email or password"):
        await use_case.execute(
            LoginInputDTO(email="viewer.integration@techpanel.dev", password="wrong")
        )
