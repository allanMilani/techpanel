from dataclasses import dataclass
from typing import Literal
from uuid import UUID


@dataclass(slots=True, frozen=True)
class MyProfileOutputDTO:
    email: str
    display_name: str | None
    has_github_token: bool


GitHubTokenPatch = str | Literal["keep"] | Literal["clear"]
DisplayNamePatch = str | None | Literal["keep"]


@dataclass(slots=True, frozen=True)
class UpdateMyProfileInputDTO:
    user_id: UUID
    display_name: DisplayNamePatch = "keep"
    github_token: GitHubTokenPatch = "keep"
