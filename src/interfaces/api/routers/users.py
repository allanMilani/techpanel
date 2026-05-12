from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.application.dtos.user_profile_dto import (
    DisplayNamePatch,
    GitHubTokenPatch,
    UpdateMyProfileInputDTO,
)
from src.application.use_cases.github.list_my_github_repositories import (
    ListMyGitHubRepositories,
)
from src.application.use_cases.github.search_my_github_refs import SearchMyGitHubRefs
from src.application.use_cases.users.get_my_profile import GetMyProfile
from src.application.use_cases.users.update_my_profile import UpdateMyProfile
from src.interfaces.api.dependencies import (
    CurrentUser,
    get_current_user,
)
from src.interfaces.api.dependencies.pagination import Pagination, get_pagination
from src.interfaces.api.dependencies.users import (
    get_get_my_profile_use_case,
    get_list_my_github_repositories_use_case,
    get_search_my_github_refs_use_case,
    get_update_my_profile_use_case,
)
from src.interfaces.api.schemas.github import GitHubRefsResponse, GitHubRepositoryResponse
from src.interfaces.api.schemas.paged_lists import GitHubRepositoriesPageResponse
from src.interfaces.api.schemas.user_profile import ProfilePatchBody, ProfileResponse

router = APIRouter(prefix="/users", tags=["users"])


def _patch_body_to_dto(user_id: UUID, body: ProfilePatchBody) -> UpdateMyProfileInputDTO:
    display_patch: DisplayNamePatch = "keep"
    if "display_name" in body.model_fields_set:
        display_patch = body.display_name

    token_patch: GitHubTokenPatch = "keep"
    if "github_token" in body.model_fields_set:
        raw = body.github_token
        if raw is None or str(raw).strip() == "":
            token_patch = "clear"
        else:
            token_patch = str(raw).strip()

    return UpdateMyProfileInputDTO(
        user_id=user_id,
        display_name=display_patch,
        github_token=token_patch,
    )


@router.get(
    "/me/profile",
    response_model=ProfileResponse,
    status_code=status.HTTP_200_OK,
)
async def get_my_profile(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    use_case: Annotated[GetMyProfile, Depends(get_get_my_profile_use_case)],
) -> ProfileResponse:
    out = await use_case.execute(UUID(user.sub))
    return ProfileResponse(
        email=out.email,
        display_name=out.display_name,
        has_github_token=out.has_github_token,
    )


@router.patch(
    "/me/profile",
    response_model=ProfileResponse,
    status_code=status.HTTP_200_OK,
)
async def patch_my_profile(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    body: ProfilePatchBody,
    use_case: Annotated[UpdateMyProfile, Depends(get_update_my_profile_use_case)],
) -> ProfileResponse:
    dto = _patch_body_to_dto(UUID(user.sub), body)
    out = await use_case.execute(dto)
    return ProfileResponse(
        email=out.email,
        display_name=out.display_name,
        has_github_token=out.has_github_token,
    )


@router.get(
    "/me/github/repos",
    response_model=GitHubRepositoriesPageResponse,
    status_code=status.HTTP_200_OK,
)
async def list_my_github_repositories(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    pagination: Annotated[Pagination, Depends(get_pagination)],
    use_case: Annotated[
        ListMyGitHubRepositories,
        Depends(get_list_my_github_repositories_use_case),
    ],
    q: str = Query(default=""),
) -> GitHubRepositoriesPageResponse:
    items, total = await use_case.execute(
        UUID(user.sub), q, pagination.page, pagination.per_page
    )
    total_pages = (
        0
        if total == 0
        else (total + pagination.per_page - 1) // pagination.per_page
    )
    return GitHubRepositoriesPageResponse(
        items=[GitHubRepositoryResponse(full_name=i.full_name) for i in items],
        total=total,
        page=pagination.page,
        per_page=pagination.per_page,
        total_pages=total_pages,
    )


@router.get(
    "/me/github/repos/{repository:path}/refs",
    response_model=GitHubRefsResponse,
    status_code=status.HTTP_200_OK,
)
async def search_my_github_refs(
    repository: str,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    use_case: Annotated[
        SearchMyGitHubRefs,
        Depends(get_search_my_github_refs_use_case),
    ],
    q: str = Query(default=""),
    limit: int = Query(default=50, ge=1, le=100),
) -> GitHubRefsResponse:
    out = await use_case.execute(UUID(user.sub), repository, q, limit)
    return GitHubRefsResponse(branches=out.branches, tags=out.tags)
