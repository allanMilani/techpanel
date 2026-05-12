import pytest

from src.application import ConflictAppError
from src.application.dtos import RegisterUserInputDTO
from src.application.use_cases.auth.register_user import RegisterUser
from src.domain.entities.user import User
from src.domain.value_objects.user_role import UserRole


class _MemoryUserRepo:
    def __init__(self) -> None:
        self.items: dict[str, User] = {}

    async def create(self, user: User) -> User:
        self.items[user.email] = user
        return user

    async def get_by_id(self, user_id):
        return next((u for u in self.items.values() if u.id == user_id), None)

    async def get_by_email(self, email: str) -> User | None:
        return self.items.get(email)

    async def update(self, user: User) -> User:
        self.items[user.email] = user
        return user


class _FakePasswordHasher:
    def hash(self, raw_password: str) -> str:
        return f"hashed::{raw_password}"

    def verify(self, raw_password: str, password_hash: str) -> bool:
        return password_hash == f"hashed::{raw_password}"


@pytest.mark.asyncio
async def test_register_user_success() -> None:
    user_repo = _MemoryUserRepo()
    use_case = RegisterUser(user_repo=user_repo, password_hasher=_FakePasswordHasher())

    out = await use_case.execute(
        RegisterUserInputDTO(
            email="  New.User@TechPanel.dev ",
            password="secret123",
            display_name="  Ana  ",
        )
    )

    assert out.email == "new.user@techpanel.dev"
    assert out.role == UserRole.VIEWER.value
    assert user_repo.items[out.email].password_hash == "hashed::secret123"
    assert user_repo.items[out.email].display_name == "Ana"


@pytest.mark.asyncio
async def test_register_user_rejects_existing_email() -> None:
    user_repo = _MemoryUserRepo()
    await user_repo.create(
        User.create(
            email="existing@techpanel.dev",
            password_hash="hashed::old",
            role=UserRole.VIEWER,
        )
    )
    use_case = RegisterUser(user_repo=user_repo, password_hasher=_FakePasswordHasher())

    with pytest.raises(ConflictAppError, match="Email already registered"):
        await use_case.execute(
            RegisterUserInputDTO(email="existing@techpanel.dev", password="secret123")
        )
