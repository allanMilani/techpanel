import pytest

from src.application import UnauthorizedAppError
from src.application.dtos import LoginInputDTO
from src.application.use_cases.auth.login import Login
from src.domain.entities.user import User
from src.domain.value_objects.user_role import UserRole

from tests.unit.application.fakes import FakePasswordHasher, FakeTokenService


class UserRepoStub:
    def __init__(self, user: User | None) -> None:
        self.user = user

    async def create(self, user: User) -> User:
        raise NotImplementedError

    async def get_by_id(self, id):
        raise NotImplementedError

    async def get_by_email(self, email: str) -> User | None:
        if self.user is None:
            return None
        return self.user if self.user.email == email else None


@pytest.mark.asyncio
async def test_login_success() -> None:
    user = User.create("admin@techpanel.local", "stored-hash", UserRole.ADMIN)
    use_case = Login(
        UserRepoStub(user),
        FakePasswordHasher("secret"),
        FakeTokenService(),
    )
    out = await use_case.execute(
        LoginInputDTO(email="admin@techpanel.local", password="secret")
    )
    assert out.access_token.startswith("token.")
    assert out.user_id == user.id


@pytest.mark.asyncio
async def test_login_fails_when_user_missing() -> None:
    use_case = Login(
        UserRepoStub(None),
        FakePasswordHasher(),
        FakeTokenService(),
    )
    with pytest.raises(UnauthorizedAppError):
        await use_case.execute(LoginInputDTO(email="x@y.com", password="secret"))


@pytest.mark.asyncio
async def test_login_fails_when_password_invalid() -> None:
    user = User.create("a@b.com", "hash", UserRole.ADMIN)
    use_case = Login(
        UserRepoStub(user),
        FakePasswordHasher("right"),
        FakeTokenService(),
    )
    with pytest.raises(UnauthorizedAppError):
        await use_case.execute(LoginInputDTO(email="a@b.com", password="wrong"))
