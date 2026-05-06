from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Header, Query, Response, status

from src.application.dtos.github_dto import GitHubAuthCallbackInputDTO
from src.application.use_cases.github import (
    HandleGitHubOAuthCallback,
    ListGitHubRefs,
    ListGitHubRepositories,
    StartGitHubOAuth,
)
from src.interfaces.api.dependencies import (
    CurrentUser,
    get_current_user,
    get_handle_github_oauth_callback_use_case,
    get_list_github_refs_use_case,
    get_list_github_repositories_use_case,
    get_start_github_oauth_use_case,
)
from src.interfaces.api.dependencies.pagination import Pagination, get_pagination
from src.interfaces.api.schemas.github import (
    GitHubOAuthCallbackResponse,
    GitHubOAuthStartResponse,
    GitHubRefsResponse,
    GitHubRepositoryResponse,
)
from src.interfaces.api.schemas.paged_lists import GitHubRepositoriesPageResponse

router = APIRouter(tags=["github"])


@router.get(
    "/auth/github",
    response_model=GitHubOAuthStartResponse,
    status_code=status.HTTP_200_OK,
)
async def start_github_oauth(
    response: Response,
    _: Annotated[CurrentUser, Depends(get_current_user)],
    use_case: Annotated[StartGitHubOAuth, Depends(get_start_github_oauth_use_case)],
) -> GitHubOAuthStartResponse:
    out = await use_case.execute()
    response.set_cookie(
        key="github_oauth_state",
        value=out.state,
        httponly=True,
        samesite="lax",
        max_age=600,
    )
    return GitHubOAuthStartResponse(
        authorization_url=out.authorization_url,
        state=out.state,
    )


@router.get(
    "/auth/github/callback",
    response_model=GitHubOAuthCallbackResponse,
    status_code=status.HTTP_200_OK,
)
async def github_oauth_callback(
    response: Response,
    _: Annotated[CurrentUser, Depends(get_current_user)],
    code: str = Query(...),
    state: str = Query(...),
    cookie_state: str | None = Cookie(default=None, alias="github_oauth_state"),
    use_case: Annotated[
        HandleGitHubOAuthCallback,
        Depends(get_handle_github_oauth_callback_use_case),
    ] = None,
) -> GitHubOAuthCallbackResponse:
    out = await use_case.execute(
        GitHubAuthCallbackInputDTO(code=code, state=state),
        expected_state=cookie_state or "",
    )
    response.delete_cookie("github_oauth_state")
    return GitHubOAuthCallbackResponse(
        access_token=out.access_token,
        token_type=out.token_type,
    )


@router.get(
    "/github/repos",
    response_model=GitHubRepositoriesPageResponse,
    status_code=status.HTTP_200_OK,
)
async def list_github_repositories(
    _: Annotated[CurrentUser, Depends(get_current_user)],
    pagination: Annotated[Pagination, Depends(get_pagination)],
    github_token: str = Header(..., alias="X-GitHub-Token"),
    use_case: Annotated[
        ListGitHubRepositories,
        Depends(get_list_github_repositories_use_case),
    ] = None,
) -> GitHubRepositoriesPageResponse:
    repos = await use_case.execute(access_token=github_token)
    total = len(repos)
    offset = (pagination.page - 1) * pagination.per_page
    slice_repos = repos[offset : offset + pagination.per_page]
    total_pages = 0 if total == 0 else (total + pagination.per_page - 1) // pagination.per_page
    return GitHubRepositoriesPageResponse(
        items=[GitHubRepositoryResponse(full_name=repo.full_name) for repo in slice_repos],
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=total_pages,
    )


@router.get(
    "/github/repos/{repository:path}/refs",
    response_model=GitHubRefsResponse,
    status_code=status.HTTP_200_OK,
)
async def list_github_refs(
    repository: str,
    _: Annotated[CurrentUser, Depends(get_current_user)],
    github_token: str = Header(..., alias="X-GitHub-Token"),
    use_case: Annotated[ListGitHubRefs, Depends(get_list_github_refs_use_case)] = None,
) -> GitHubRefsResponse:
    refs = await use_case.execute(access_token=github_token, repository=repository)
    return GitHubRefsResponse(branches=refs.branches, tags=refs.tags)
