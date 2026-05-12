from typing import Annotated

from fastapi import Depends

from src.application.use_cases.github.list_my_github_repositories import (
    ListMyGitHubRepositories,
)
from src.application.use_cases.github.search_my_github_refs import SearchMyGitHubRefs
from src.application.use_cases.users.get_my_profile import GetMyProfile
from src.application.use_cases.users.update_my_profile import UpdateMyProfile
from src.domain.ports.repositories import IUserRepository
from src.domain.ports.services import IGitHubService, IKeyCipher
from src.interfaces.api.dependencies.core import get_user_repository
from src.interfaces.api.dependencies.github import get_github_service
from src.interfaces.api.dependencies.servers import get_key_cipher


def get_get_my_profile_use_case(
    user_repo: Annotated[IUserRepository, Depends(get_user_repository)],
) -> GetMyProfile:
    return GetMyProfile(user_repo)


def get_update_my_profile_use_case(
    user_repo: Annotated[IUserRepository, Depends(get_user_repository)],
    key_cipher: Annotated[IKeyCipher, Depends(get_key_cipher)],
) -> UpdateMyProfile:
    return UpdateMyProfile(user_repo, key_cipher)


def get_list_my_github_repositories_use_case(
    user_repo: Annotated[IUserRepository, Depends(get_user_repository)],
    key_cipher: Annotated[IKeyCipher, Depends(get_key_cipher)],
    github_service: Annotated[IGitHubService, Depends(get_github_service)],
) -> ListMyGitHubRepositories:
    return ListMyGitHubRepositories(user_repo, key_cipher, github_service)


def get_search_my_github_refs_use_case(
    user_repo: Annotated[IUserRepository, Depends(get_user_repository)],
    key_cipher: Annotated[IKeyCipher, Depends(get_key_cipher)],
    github_service: Annotated[IGitHubService, Depends(get_github_service)],
) -> SearchMyGitHubRefs:
    return SearchMyGitHubRefs(user_repo, key_cipher, github_service)
