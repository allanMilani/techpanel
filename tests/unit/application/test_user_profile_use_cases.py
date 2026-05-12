from dataclasses import replace
from uuid import uuid4

import pytest

from src.application.dtos.user_profile_dto import UpdateMyProfileInputDTO
from src.application.use_cases.users.get_my_profile import GetMyProfile
from src.application.use_cases.users.update_my_profile import UpdateMyProfile
from src.domain.entities.user import User
from src.domain.value_objects.user_role import UserRole


class _MemUserRepo:
    def __init__(self, user: User) -> None:
        self.user = user

    async def create(self, user: User) -> User:
        self.user = user
        return user

    async def get_by_id(self, user_id):
        return self.user if self.user.id == user_id else None

    async def get_by_email(self, _email: str):
        return None

    async def update(self, user: User) -> User:
        self.user = user
        return user


class _FakeCipher:
    def encrypt(self, plain_text: str) -> str:
        return f"enc::{plain_text}"

    def decrypt(self, cipher_text: str) -> str:
        return cipher_text.removeprefix("enc::")


@pytest.mark.asyncio
async def test_get_my_profile() -> None:
    uid = uuid4()
    u = replace(
        User.create("x@y.dev", "h", UserRole.VIEWER, display_name="Nome"),
        id=uid,
    )
    repo = _MemUserRepo(u)
    uc = GetMyProfile(repo)
    out = await uc.execute(uid)
    assert out.email == "x@y.dev"
    assert out.display_name == "Nome"
    assert out.has_github_token is False


@pytest.mark.asyncio
async def test_update_my_profile_sets_token_and_name() -> None:
    uid = uuid4()
    u = replace(
        User.create("x@y.dev", "h", UserRole.VIEWER),
        id=uid,
    )
    repo = _MemUserRepo(u)
    cipher = _FakeCipher()
    uc = UpdateMyProfile(repo, cipher)
    out = await uc.execute(
        UpdateMyProfileInputDTO(
            user_id=uid,
            display_name="Novo",
            github_token="ghp_secret",
        )
    )
    assert out.display_name == "Novo"
    assert out.has_github_token is True
    assert repo.user.github_token_enc == "enc::ghp_secret"
