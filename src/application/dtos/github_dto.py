from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class GitHubAuthStartOutputDTO:
    authorization_url: str
    state: str


@dataclass(slots=True, frozen=True)
class GitHubAuthCallbackInputDTO:
    code: str
    state: str


@dataclass(slots=True, frozen=True)
class GitHubAuthCallbackOutputDTO:
    access_token: str
    token_type: str


@dataclass(slots=True, frozen=True)
class GitHubRepositoryDTO:
    full_name: str


@dataclass(slots=True, frozen=True)
class GitHubRefsDTO:
    branches: list[str]
    tags: list[str]
