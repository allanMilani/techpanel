from typing import Annotated

from fastapi import Depends

from src.application.use_cases.github import (
    HandleGitHubOAuthCallback,
    ListGitHubRefs,
    ListGitHubRepositories,
    StartGitHubOAuth,
)
from src.domain.ports.services import IGitHubService
from src.infrastructure.config.settings import get_settings
from src.infrastructure.services.pygithub_service import PyGitHubService


def get_github_service() -> IGitHubService:
    settings = get_settings()
    if (
        not settings.github_client_id
        or not settings.github_client_secret
        or not settings.github_oauth_callback_url
    ):
        raise RuntimeError("GitHub OAuth settings are not configured")

    return PyGitHubService(
        client_id=settings.github_client_id,
        client_secret=settings.github_client_secret,
        callback_url=settings.github_oauth_callback_url,
    )


def get_start_github_oauth_use_case(
    github_service: Annotated[IGitHubService, Depends(get_github_service)],
) -> StartGitHubOAuth:
    return StartGitHubOAuth(github_service=github_service)


def get_handle_github_oauth_callback_use_case(
    github_service: Annotated[IGitHubService, Depends(get_github_service)],
) -> HandleGitHubOAuthCallback:
    return HandleGitHubOAuthCallback(github_service=github_service)


def get_list_github_repositories_use_case(
    github_service: Annotated[IGitHubService, Depends(get_github_service)],
) -> ListGitHubRepositories:
    return ListGitHubRepositories(github_service=github_service)


def get_list_github_refs_use_case(
    github_service: Annotated[IGitHubService, Depends(get_github_service)],
) -> ListGitHubRefs:
    return ListGitHubRefs(github_service=github_service)
